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
import { scoreSentiment, type SentimentScore } from "./claude";

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
  }>;
}

// ABI for the report payload sent to SentimentOracle._processReport
const REPORT_PARAMS = parseAbiParameters(
  "string project, uint8 score, uint32 totalMentions, uint32 positive, uint32 negative, uint32 neutral, string summary"
);

export function onHttpTrigger(runtime: Runtime<Config>, payload: HTTPPayload): string {
  runtime.log("=== SignalBox Sentiment Oracle: HTTP Trigger ===");

  try {
    // Parse optional project filter from trigger payload
    let targetProjects = runtime.config.projects;
    if (payload.input && payload.input.length > 0) {
      const input = decodeJson(payload.input) as TriggerPayload;
      if (input.project) {
        targetProjects = [input.project];
      }
    }

    runtime.log(`[Step 1] Updating sentiment for: ${targetProjects.join(", ")}`);

    const evmConfig = runtime.config.evms[0];
    const network = getNetwork({
      chainFamily: "evm",
      chainSelectorName: evmConfig.chainSelectorName,
      isTestnet: true,
    });

    if (!network) {
      throw new Error(`Unknown chain: ${evmConfig.chainSelectorName}`);
    }

    const evmClient = new cre.capabilities.EVMClient(network.chainSelector.selector);
    const results: string[] = [];

    for (const project of targetProjects) {
      try {
        runtime.log(`\n--- Processing: ${project} ---`);

        // Step 2: Fetch sentiment data from SignalBox API
        runtime.log("[Step 2] Fetching from SignalBox API...");
        const feedbackData = fetchSentiment(runtime, project);

        if (feedbackData.total_mentions === 0) {
          runtime.log(`[Step 2] No mentions for ${project}, skipping`);
          continue;
        }

        runtime.log(`[Step 2] Got ${feedbackData.total_mentions} mentions`);

        // Step 3: Score with Claude AI
        runtime.log("[Step 3] Scoring with Claude AI...");
        const feedbackJson = JSON.stringify(feedbackData.items.slice(0, 20));
        const score = scoreSentiment(runtime, project, feedbackJson);

        // Step 4: Encode and write on-chain
        runtime.log("[Step 4] Writing to SentimentOracle contract...");

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

        const writeResult = evmClient
          .writeReport(runtime, {
            receiver: evmConfig.oracleAddress,
            report: reportResponse,
            gasConfig: {
              gasLimit: evmConfig.gasLimit,
            },
          })
          .result();

        if (writeResult.txStatus === TxStatus.SUCCESS) {
          const txHash = bytesToHex(writeResult.txHash || new Uint8Array(32));
          runtime.log(`[Step 4] ${project}: score=${score.score} tx=${txHash}`);
          results.push(`${project}:${score.score}:${txHash}`);
        } else {
          runtime.log(`[Step 4] ${project}: tx failed (${writeResult.txStatus})`);
          results.push(`${project}:FAILED`);
        }
      } catch (projectErr) {
        const msg = projectErr instanceof Error ? projectErr.message : String(projectErr);
        runtime.log(`[ERROR] ${project} failed: ${msg}`);
        results.push(`${project}:ERROR`);
      }
    }

    runtime.log("\n=== Sentiment Oracle Update Complete ===");
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
