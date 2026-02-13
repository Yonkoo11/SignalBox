import {
  cre,
  ok,
  consensusIdenticalAggregation,
  type Runtime,
  type HTTPSendRequester,
} from "@chainlink/cre-sdk";

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

interface ClaudeRequest {
  model: string;
  max_tokens: number;
  messages: Array<{
    role: string;
    content: string;
  }>;
}

interface ClaudeApiResponse {
  content?: Array<{ text?: string }>;
  id?: string;
}

export interface SentimentScore {
  score: number;        // 0-100
  positive: number;     // count
  negative: number;     // count
  neutral: number;      // count
  summary: string;
}

const SYSTEM_PROMPT = `You are a sentiment analysis system for crypto project community feedback from Twitter/X.

Given a JSON array of classified feedback items, produce a sentiment score and summary.

OUTPUT FORMAT (CRITICAL):
- Respond with ONLY a single JSON object:
  {"score": <0-100>, "positive": <count>, "negative": <count>, "neutral": <count>, "summary": "<1-2 sentence summary>"}

SCORING RULES:
- 0 = extremely negative (all bugs, complaints, outrage)
- 50 = neutral/mixed
- 100 = extremely positive (all praise, excitement)
- Weight by engagement: high-engagement items matter more
- "positive" = praise + feature_request items
- "negative" = bug + complaint items
- "neutral" = question items

OUTPUT MUST be valid minified JSON. No markdown, no backticks, no prose.`;

export function scoreSentiment(
  runtime: Runtime<Config>,
  project: string,
  feedbackJson: string
): SentimentScore {
  runtime.log(`[Claude] Scoring sentiment for ${project}...`);

  const apiKey = runtime.getSecret({ id: "ANTHROPIC_API_KEY" }).result();
  const httpClient = new cre.capabilities.HTTPClient();

  const result = httpClient
    .sendRequest(
      runtime,
      buildClaudeRequest(project, feedbackJson, apiKey.value),
      consensusIdenticalAggregation<SentimentScore>()
    )(runtime.config)
    .result();

  runtime.log(`[Claude] Score: ${result.score}/100 | +${result.positive} -${result.negative} ~${result.neutral}`);
  return result;
}

const buildClaudeRequest =
  (project: string, feedbackJson: string, apiKey: string) =>
  (sendRequester: HTTPSendRequester, config: Config): SentimentScore => {
    const requestData: ClaudeRequest = {
      model: config.anthropicModel,
      max_tokens: 256,
      messages: [
        { role: "user", content: `${SYSTEM_PROMPT}\n\nProject: ${project}\n\nFeedback data:\n${feedbackJson}` },
      ],
    };

    const bodyBytes = new TextEncoder().encode(JSON.stringify(requestData));
    const body = Buffer.from(bodyBytes).toString("base64");

    const req = {
      url: "https://api.anthropic.com/v1/messages",
      method: "POST" as const,
      body,
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      cacheSettings: {
        store: true,
        maxAge: "300s",
      },
    };

    const resp = sendRequester.sendRequest(req).result();
    const bodyText = new TextDecoder().decode(resp.body);

    if (!ok(resp)) {
      throw new Error(`Claude API error: ${resp.statusCode} - ${bodyText}`);
    }

    const apiResponse = JSON.parse(bodyText) as ClaudeApiResponse;
    const text = apiResponse?.content?.[0]?.text;

    if (!text) {
      throw new Error("Malformed Claude response: missing text");
    }

    const jsonMatch = text.match(/\{[^{}]*"score"\s*:\s*\d+[^{}]*\}/);
    if (!jsonMatch) {
      throw new Error(`Could not find JSON in Claude response: ${text}`);
    }

    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(jsonMatch[0]);
    } catch {
      throw new Error(`Invalid JSON in Claude response: ${jsonMatch[0]}`);
    }

    // Validate and clamp fields
    const score = Math.max(0, Math.min(100, Number(parsed.score) || 50));
    const positive = Math.max(0, Number(parsed.positive) || 0);
    const negative = Math.max(0, Number(parsed.negative) || 0);
    const neutral = Math.max(0, Number(parsed.neutral) || 0);
    const summary = String(parsed.summary || "No summary available").slice(0, 280);

    return { score, positive, negative, neutral, summary };
  };
