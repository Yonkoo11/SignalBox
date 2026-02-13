// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ReceiverTemplate} from "./interfaces/ReceiverTemplate.sol";

/// @title SentimentOracle - On-chain social intelligence feed powered by Chainlink CRE
/// @notice Receives AI-classified community feedback data via CRE workflows
/// @dev Emits RiskAlert when sentiment drops significantly between updates
contract SentimentOracle is ReceiverTemplate {
    struct SentimentData {
        uint8 score;          // 0-100 sentiment score
        uint32 totalMentions;
        uint32 positive;      // praise + feature requests
        uint32 negative;      // bugs + complaints
        uint32 neutral;       // questions
        string summary;
        uint256 timestamp;
    }

    /// @notice Threshold for risk alert: score drop of this many points triggers alert
    uint8 public constant RISK_THRESHOLD = 15;

    // project name => latest sentiment
    mapping(string => SentimentData) public latestSentiment;
    // project name => historical scores
    mapping(string => SentimentData[]) public sentimentHistory;
    // tracked projects
    string[] public trackedProjects;
    mapping(string => bool) public isTracked;

    event SentimentUpdated(
        string indexed project,
        uint8 score,
        uint32 totalMentions,
        string summary,
        uint256 timestamp
    );
    event ProjectAdded(string project);
    event RiskAlert(
        string indexed project,
        uint8 previousScore,
        uint8 newScore,
        uint8 dropSize,
        uint256 timestamp
    );

    constructor(
        address _forwarderAddress
    ) ReceiverTemplate(_forwarderAddress) {}

    /// @notice Called by CRE workflow via ReceiverTemplate.onReport
    /// @dev Decodes report as (string project, uint8 score, uint32 total, uint32 pos, uint32 neg, uint32 neutral, string summary)
    function _processReport(bytes calldata report) internal override {
        (
            string memory project,
            uint8 score,
            uint32 totalMentions,
            uint32 positive,
            uint32 negative,
            uint32 neutral,
            string memory summary
        ) = abi.decode(report, (string, uint8, uint32, uint32, uint32, uint32, string));

        require(score <= 100, "Score must be 0-100");

        if (!isTracked[project]) {
            trackedProjects.push(project);
            isTracked[project] = true;
            emit ProjectAdded(project);
        }

        // Check for risk alert before updating
        uint8 previousScore = latestSentiment[project].score;
        bool hasPrevious = latestSentiment[project].timestamp > 0;

        SentimentData memory data = SentimentData({
            score: score,
            totalMentions: totalMentions,
            positive: positive,
            negative: negative,
            neutral: neutral,
            summary: summary,
            timestamp: block.timestamp
        });

        latestSentiment[project] = data;
        sentimentHistory[project].push(data);

        emit SentimentUpdated(project, score, totalMentions, summary, block.timestamp);

        // Emit risk alert if score dropped significantly
        if (hasPrevious && previousScore > score) {
            uint8 drop = previousScore - score;
            if (drop >= RISK_THRESHOLD) {
                emit RiskAlert(project, previousScore, score, drop, block.timestamp);
            }
        }
    }

    // ──────────────────────────────────────────────
    // Public read functions
    // ──────────────────────────────────────────────

    function getSentiment(
        string calldata project
    ) external view returns (SentimentData memory) {
        return latestSentiment[project];
    }

    function getHistory(
        string calldata project,
        uint256 count
    ) external view returns (SentimentData[] memory) {
        SentimentData[] storage history = sentimentHistory[project];
        uint256 len = history.length;
        if (count > len) count = len;

        SentimentData[] memory result = new SentimentData[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = history[len - count + i];
        }
        return result;
    }

    function getTrackedProjects() external view returns (string[] memory) {
        return trackedProjects;
    }

    function getHistoryLength(
        string calldata project
    ) external view returns (uint256) {
        return sentimentHistory[project].length;
    }
}
