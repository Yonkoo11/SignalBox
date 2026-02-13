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

// --- Step 2: Classification types ---

export interface ClassifiedItem {
  text: string;
  category: string;       // bug | feature_request | complaint | praise | question
  priority: string;       // high | medium | low
  botProbability: number; // 0-100
  engagement: number;
  author: string;
}

export interface ClassificationResult {
  items: ClassifiedItem[];
  totalClassified: number;
}

// --- Step 3: Aggregation types ---

export interface SentimentScore {
  score: number;        // 0-100
  positive: number;     // count
  negative: number;     // count
  neutral: number;      // count
  summary: string;
  topIssues: string[];  // top 3 issues by engagement
  riskFlag: boolean;    // AI thinks sentiment is dangerously low
}

// --- Prompts ---

const CLASSIFY_PROMPT = `You are a feedback classification system for crypto project community posts from Twitter/X.

Given a JSON array of raw community posts, classify EACH item.

For EACH item, determine:
- category: one of "bug", "feature_request", "complaint", "praise", "question"
- priority: "high" (security/outage/money-at-risk), "medium" (usability/feature gaps), "low" (general feedback)
- botProbability: 0-100 (0 = clearly human, 100 = clearly bot/spam)

OUTPUT FORMAT (CRITICAL):
Respond with ONLY a JSON object:
{"items": [{"text": "original text", "category": "bug", "priority": "high", "botProbability": 5, "engagement": 142, "author": "username"}, ...], "totalClassified": <count>}

CLASSIFICATION RULES:
- "bug" = broken functionality, errors, crashes, unexpected behavior
- "feature_request" = wants something new or improved
- "complaint" = unhappy about existing behavior (not broken, just disliked)
- "praise" = positive feedback, appreciation, excitement
- "question" = asking for help or information
- Priority "high" only if: security risk, funds at risk, service outage, or >50K engagement
- Bot signals: generic text, excessive emojis, no context, suspicious patterns

OUTPUT MUST be valid minified JSON. No markdown, no backticks, no prose.`;

const AGGREGATE_PROMPT = `You are a sentiment aggregation system for crypto project community feedback.

Given CLASSIFIED feedback items (already categorized by AI), produce an overall sentiment score, summary, and risk assessment.

OUTPUT FORMAT (CRITICAL):
Respond with ONLY a JSON object:
{"score": <0-100>, "positive": <count>, "negative": <count>, "neutral": <count>, "summary": "<1-2 sentence summary>", "topIssues": ["issue 1", "issue 2", "issue 3"], "riskFlag": <true/false>}

SCORING RULES:
- 0 = extremely negative (all bugs, complaints, outrage)
- 50 = neutral/mixed
- 100 = extremely positive (all praise, excitement)
- Weight by engagement: high-engagement items matter more
- Filter out items with botProbability > 70 (don't count bots)
- "positive" = count of praise + feature_request items (excluding bots)
- "negative" = count of bug + complaint items (excluding bots)
- "neutral" = count of question items (excluding bots)

RISK ASSESSMENT:
- riskFlag = true if: score < 40, OR >50% of items are bugs/complaints, OR any high-priority bug exists
- topIssues = the 3 most important issues by engagement (bugs and complaints first)

OUTPUT MUST be valid minified JSON. No markdown, no backticks, no prose.`;

// --- Step 2: Classify feedback items ---

export function classifyFeedback(
  runtime: Runtime<Config>,
  project: string,
  rawItems: string
): ClassificationResult {
  runtime.log(`[Claude] Step 2: Classifying feedback for ${project}...`);

  const apiKey = runtime.getSecret({ id: "ANTHROPIC_API_KEY" }).result();
  const httpClient = new cre.capabilities.HTTPClient();

  const result = httpClient
    .sendRequest(
      runtime,
      buildClassifyRequest(project, rawItems, apiKey.value),
      consensusIdenticalAggregation<ClassificationResult>()
    )(runtime.config)
    .result();

  runtime.log(`[Claude] Classified ${result.totalClassified} items for ${project}`);
  return result;
}

// --- Step 3: Aggregate + Risk Assessment ---

export function aggregateSentiment(
  runtime: Runtime<Config>,
  project: string,
  classifiedJson: string
): SentimentScore {
  runtime.log(`[Claude] Step 3: Aggregating sentiment for ${project}...`);

  const apiKey = runtime.getSecret({ id: "ANTHROPIC_API_KEY" }).result();
  const httpClient = new cre.capabilities.HTTPClient();

  const result = httpClient
    .sendRequest(
      runtime,
      buildAggregateRequest(project, classifiedJson, apiKey.value),
      consensusIdenticalAggregation<SentimentScore>()
    )(runtime.config)
    .result();

  runtime.log(`[Claude] Score: ${result.score}/100 | +${result.positive} -${result.negative} ~${result.neutral} | risk=${result.riskFlag}`);
  if (result.topIssues.length > 0) {
    runtime.log(`[Claude] Top issues: ${result.topIssues.join("; ")}`);
  }
  return result;
}

// --- HTTP request builders ---

const buildClassifyRequest =
  (project: string, rawItems: string, apiKey: string) =>
  (sendRequester: HTTPSendRequester, config: Config): ClassificationResult => {
    const requestData: ClaudeRequest = {
      model: config.anthropicModel,
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: `${CLASSIFY_PROMPT}\n\nProject: ${project}\n\nRaw posts:\n${rawItems}`,
        },
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
      throw new Error(`Claude API error (classify): ${resp.statusCode} - ${bodyText}`);
    }

    const apiResponse = JSON.parse(bodyText) as ClaudeApiResponse;
    const text = apiResponse?.content?.[0]?.text;

    if (!text) {
      throw new Error("Malformed Claude response (classify): missing text");
    }

    // Parse the JSON from Claude's response
    const jsonMatch = text.match(/\{[\s\S]*"items"\s*:\s*\[[\s\S]*\][\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error(`Could not find JSON in classify response: ${text.slice(0, 200)}`);
    }

    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(jsonMatch[0]);
    } catch {
      throw new Error(`Invalid JSON in classify response: ${jsonMatch[0].slice(0, 200)}`);
    }

    const items = (parsed.items as ClassifiedItem[]) || [];
    return {
      items: items.map((item) => ({
        text: String(item.text || ""),
        category: String(item.category || "question"),
        priority: String(item.priority || "low"),
        botProbability: Math.max(0, Math.min(100, Number(item.botProbability) || 0)),
        engagement: Math.max(0, Number(item.engagement) || 0),
        author: String(item.author || "unknown"),
      })),
      totalClassified: items.length,
    };
  };

const buildAggregateRequest =
  (project: string, classifiedJson: string, apiKey: string) =>
  (sendRequester: HTTPSendRequester, config: Config): SentimentScore => {
    const requestData: ClaudeRequest = {
      model: config.anthropicModel,
      max_tokens: 512,
      messages: [
        {
          role: "user",
          content: `${AGGREGATE_PROMPT}\n\nProject: ${project}\n\nClassified feedback:\n${classifiedJson}`,
        },
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
      throw new Error(`Claude API error (aggregate): ${resp.statusCode} - ${bodyText}`);
    }

    const apiResponse = JSON.parse(bodyText) as ClaudeApiResponse;
    const text = apiResponse?.content?.[0]?.text;

    if (!text) {
      throw new Error("Malformed Claude response (aggregate): missing text");
    }

    const jsonMatch = text.match(/\{[^{}]*"score"\s*:\s*\d+[^{}]*\}/);
    if (!jsonMatch) {
      throw new Error(`Could not find JSON in aggregate response: ${text.slice(0, 200)}`);
    }

    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(jsonMatch[0]);
    } catch {
      throw new Error(`Invalid JSON in aggregate response: ${jsonMatch[0].slice(0, 200)}`);
    }

    const score = Math.max(0, Math.min(100, Number(parsed.score) || 50));
    const positive = Math.max(0, Number(parsed.positive) || 0);
    const negative = Math.max(0, Number(parsed.negative) || 0);
    const neutral = Math.max(0, Number(parsed.neutral) || 0);
    const summary = String(parsed.summary || "No summary available").slice(0, 280);
    const riskFlag = Boolean(parsed.riskFlag);

    // Parse topIssues array
    let topIssues: string[] = [];
    if (Array.isArray(parsed.topIssues)) {
      topIssues = (parsed.topIssues as string[])
        .filter((s) => typeof s === "string")
        .slice(0, 3)
        .map((s) => s.slice(0, 120));
    }

    return { score, positive, negative, neutral, summary, topIssues, riskFlag };
  };
