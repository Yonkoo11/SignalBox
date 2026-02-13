import {
  cre,
  type Runtime,
  type HTTPPayload,
  getNetwork,
  bytesToHex,
  hexToBase64,
  TxStatus,
  ok,
  consensusIdenticalAggregation,
  decodeJson,
  type HTTPSendRequester,
} from "@chainlink/cre-sdk";
import { encodeAbiParameters, parseAbiParameters } from "viem";
import {
  classifyFeedback,
  aggregateSentiment,
  type SentimentScore,
  type ClassificationResult,
} from "./claude";

type Config = {
  signalboxApiUrl: string;
  anthropicModel: string;
  projects: string[];
  evms: Array<{
    oracleAddress: string;
    chainSelectorName: string;
    gasLimit: string;
  }>;
};

interface TriggerPayload {
  project?: string; // optional: update specific project, or all if omitted
}

interface SignalBoxResponse {
  project: string;
  period: string;
  total_mentions: number;
  breakdown: {
    praise: number;
    feature_request: number;
    question: number;
    bug: number;
    complaint: number;
  };
  items: Array<{
    text: string;
    category: string;
    priority: string;
    engagement: number;
    author: string;
    followers: number;
    timestamp: string;
  }>;
}

// ABI for the report payload sent to SentimentOracle._processReport
const REPORT_PARAMS = parseAbiParameters(
  "string project, uint8 score, uint32 totalMentions, uint32 positive, uint32 negative, uint32 neutral, string summary"
);

export function onHttpTrigger(runtime: Runtime<Config>, payload: HTTPPayload): string {
  runtime.log("=== SignalBox Sentiment Oracle v2: HTTP Trigger ===");

  try {
    // Parse project from trigger payload.
    // CRE has a per-workflow HTTP call limit (5 in simulator). The v2 pipeline uses
    // 3 HTTP calls per project (fetch + classify + aggregate) + 1 for getSecret + 1 for writeReport,
    // so we process ONE project per invocation. For multi-project updates,
    // trigger the workflow once per project.
    let targetProjects = runtime.config.projects.slice(0, 1); // default: first project
    if (payload.input && payload.input.length > 0) {
      const input = decodeJson(payload.input) as TriggerPayload;
      if (input.project) {
        targetProjects = [input.project];
      }
    }

    runtime.log(`[Step 1] Fetching data for: ${targetProjects.join(", ")}`);
    runtime.log(`[Config] Writing to ${runtime.config.evms.length} chain(s)`);

    // Pre-build EVM clients for all configured chains
    const evmClients = runtime.config.evms.map((evm) => {
      const network = getNetwork({
        chainFamily: "evm",
        chainSelectorName: evm.chainSelectorName,
        isTestnet: true,
      });
      if (!network) {
        throw new Error(`Unknown chain: ${evm.chainSelectorName}`);
      }
      return {
        config: evm,
        client: new cre.capabilities.EVMClient(network.chainSelector.selector),
        chainName: evm.chainSelectorName,
      };
    });

    const results: string[] = [];

    for (const project of targetProjects) {
      try {
        runtime.log(`\n--- Processing: ${project} ---`);

        // Step 1: Fetch raw feedback from SignalBox API
        runtime.log("[Step 1] Fetching from SignalBox API...");
        const feedbackData = fetchSentiment(runtime, project);

        if (feedbackData.total_mentions === 0) {
          runtime.log(`[Step 1] No mentions for ${project}, skipping`);
          continue;
        }

        runtime.log(`[Step 1] Got ${feedbackData.total_mentions} mentions`);

        // Step 2: AI Classification — classify each feedback item
        runtime.log("[Step 2] Classifying feedback with Claude AI...");
        const rawItemsJson = JSON.stringify(
          feedbackData.items.slice(0, 20).map((item) => ({
            text: item.text,
            engagement: item.engagement,
            author: item.author,
            followers: item.followers,
          }))
        );
        const classified: ClassificationResult = classifyFeedback(runtime, project, rawItemsJson);

        // Log classification breakdown
        const catCounts: Record<string, number> = {};
        for (const item of classified.items) {
          catCounts[item.category] = (catCounts[item.category] || 0) + 1;
        }
        runtime.log(`[Step 2] Classification: ${JSON.stringify(catCounts)}`);

        // Step 3: AI Aggregation + Risk Assessment
        runtime.log("[Step 3] Aggregating sentiment + risk assessment...");
        const classifiedJson = JSON.stringify(classified.items);
        const score: SentimentScore = aggregateSentiment(runtime, project, classifiedJson);

        // Step 4: Conditional logging (risk detection is also in the contract)
        if (score.riskFlag) {
          runtime.log(`[Step 4] RISK FLAG for ${project}: score=${score.score}, top issues: ${score.topIssues.join("; ")}`);
        }

        // Step 5: Encode and write on-chain (all configured chains)
        runtime.log(`[Step 5] Writing to ${evmClients.length} chain(s)...`);

        const reportData = encodeAbiParameters(REPORT_PARAMS, [
          project,
          score.score,
          feedbackData.total_mentions,
          score.positive,
          score.negative,
          score.neutral,
          score.summary,
        ]);

        const reportResponse = runtime
          .report({
            encodedPayload: hexToBase64(reportData),
            encoderName: "evm",
            signingAlgo: "ecdsa",
            hashingAlgo: "keccak256",
          })
          .result();

        const txHashes: string[] = [];
        for (const evm of evmClients) {
          try {
            const writeResult = evm.client
              .writeReport(runtime, {
                receiver: evm.config.oracleAddress,
                report: reportResponse,
                gasConfig: {
                  gasLimit: evm.config.gasLimit,
                },
              })
              .result();

            if (writeResult.txStatus === TxStatus.SUCCESS) {
              const txHash = bytesToHex(writeResult.txHash || new Uint8Array(32));
              runtime.log(`[Step 5] ${project} -> ${evm.chainName}: tx=${txHash}`);
              txHashes.push(txHash);
            } else {
              runtime.log(`[Step 5] ${project} -> ${evm.chainName}: tx failed (${writeResult.txStatus})`);
            }
          } catch (chainErr) {
            const msg = chainErr instanceof Error ? chainErr.message : String(chainErr);
            runtime.log(`[Step 5] ${project} -> ${evm.chainName}: error: ${msg}`);
          }
        }

        runtime.log(`[Step 5] ${project}: score=${score.score} risk=${score.riskFlag} chains=${txHashes.length}/${evmClients.length}`);
        results.push(`${project}:${score.score}:risk=${score.riskFlag}:chains=${txHashes.length}`);
      } catch (projectErr) {
        const msg = projectErr instanceof Error ? projectErr.message : String(projectErr);
        runtime.log(`[ERROR] ${project} failed: ${msg}`);
        results.push(`${project}:ERROR`);
      }
    }

    runtime.log("\n=== Sentiment Oracle v2 Update Complete ===");
    return results.join("|");

  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    runtime.log(`[ERROR] ${msg}`);
    throw err;
  }
}

function fetchSentiment(runtime: Runtime<Config>, project: string): SignalBoxResponse {
  const httpClient = new cre.capabilities.HTTPClient();

  const result = httpClient
    .sendRequest(
      runtime,
      buildFetchRequest(project),
      consensusIdenticalAggregation<SignalBoxResponse>()
    )(runtime.config)
    .result();

  return result;
}

const buildFetchRequest =
  (project: string) =>
  (sendRequester: HTTPSendRequester, config: Config): SignalBoxResponse => {
    const url = `${config.signalboxApiUrl}/api/v1/sentiment/${project}?period=1h`;

    const req = {
      url,
      method: "GET" as const,
      headers: {
        "Content-Type": "application/json",
      },
      cacheSettings: {
        store: true,
        maxAge: "60s",
      },
    };

    const resp = sendRequester.sendRequest(req).result();
    const bodyText = new TextDecoder().decode(resp.body);

    if (!ok(resp)) {
      throw new Error(`SignalBox API error: ${resp.statusCode} - ${bodyText}`);
    }

    return JSON.parse(bodyText) as SignalBoxResponse;
  };
