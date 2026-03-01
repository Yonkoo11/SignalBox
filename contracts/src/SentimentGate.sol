// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {SentimentOracle} from "./SentimentOracle.sol";

/// @title SentimentGate - Governance actions gated by on-chain sentiment
/// @notice Demonstrates a downstream consumer of SentimentOracle data.
///         Proposals can only execute when community sentiment is healthy.
/// @dev Shows real utility: DAOs can use sentiment oracles to guard against
///      executing proposals during periods of community dissatisfaction.
contract SentimentGate {
    SentimentOracle public immutable oracle;
    address public owner;

    uint8 public sentimentThreshold; // minimum score to allow execution
    uint256 public freshnessWindow;  // max age of sentiment data in seconds

    struct Proposal {
        string description;
        string project;        // which project's sentiment to check
        address target;        // contract to call
        bytes callData;        // function call data
        uint256 createdAt;
        bool executed;
        bool cancelled;
    }

    Proposal[] public proposals;

    event ProposalCreated(uint256 indexed id, string project, string description);
    event ProposalExecuted(uint256 indexed id, uint8 sentimentScore);
    event ProposalCancelled(uint256 indexed id);
    event ThresholdUpdated(uint8 oldThreshold, uint8 newThreshold);
    event SentimentCheckFailed(uint256 indexed id, uint8 currentScore, uint8 requiredScore);

    error OnlyOwner();
    error ProposalAlreadyExecuted();
    error ProposalCancelled_();
    error SentimentTooLow(uint8 current, uint8 required);
    error SentimentDataStale(uint256 dataAge, uint256 maxAge);
    error ProposalNotFound();
    error ExecutionFailed();

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    constructor(address _oracle, uint8 _threshold, uint256 _freshnessWindow) {
        oracle = SentimentOracle(_oracle);
        owner = msg.sender;
        sentimentThreshold = _threshold;
        freshnessWindow = _freshnessWindow;
    }

    /// @notice Create a new proposal gated by a project's sentiment
    /// @param project The project whose sentiment must be above threshold
    /// @param description Human-readable description of the proposal
    /// @param target Contract address to call if sentiment check passes
    /// @param callData Encoded function call to execute
    function createProposal(
        string calldata project,
        string calldata description,
        address target,
        bytes calldata callData
    ) external onlyOwner returns (uint256 proposalId) {
        proposalId = proposals.length;
        proposals.push(Proposal({
            description: description,
            project: project,
            target: target,
            callData: callData,
            createdAt: block.timestamp,
            executed: false,
            cancelled: false
        }));
        emit ProposalCreated(proposalId, project, description);
    }

    /// @notice Execute a proposal only if community sentiment is healthy
    /// @dev Reads latest sentiment from SentimentOracle and checks:
    ///      1. Score >= threshold
    ///      2. Data is fresh (within freshnessWindow)
    function executeProposal(uint256 proposalId) external onlyOwner {
        if (proposalId >= proposals.length) revert ProposalNotFound();
        Proposal storage p = proposals[proposalId];
        if (p.executed) revert ProposalAlreadyExecuted();
        if (p.cancelled) revert ProposalCancelled_();

        // Read sentiment from oracle
        SentimentOracle.SentimentData memory sentiment = oracle.getSentiment(p.project);

        // Check freshness
        uint256 dataAge = block.timestamp - sentiment.timestamp;
        if (dataAge > freshnessWindow) {
            revert SentimentDataStale(dataAge, freshnessWindow);
        }

        // Check sentiment threshold
        if (sentiment.score < sentimentThreshold) {
            emit SentimentCheckFailed(proposalId, sentiment.score, sentimentThreshold);
            revert SentimentTooLow(sentiment.score, sentimentThreshold);
        }

        // Sentiment is healthy - execute the proposal
        p.executed = true;

        if (p.target != address(0)) {
            (bool success, ) = p.target.call(p.callData);
            if (!success) revert ExecutionFailed();
        }

        emit ProposalExecuted(proposalId, sentiment.score);
    }

    /// @notice Cancel a proposal
    function cancelProposal(uint256 proposalId) external onlyOwner {
        if (proposalId >= proposals.length) revert ProposalNotFound();
        proposals[proposalId].cancelled = true;
        emit ProposalCancelled(proposalId);
    }

    /// @notice Update the sentiment threshold
    function setThreshold(uint8 newThreshold) external onlyOwner {
        uint8 old = sentimentThreshold;
        sentimentThreshold = newThreshold;
        emit ThresholdUpdated(old, newThreshold);
    }

    /// @notice Check if a proposal can currently be executed
    /// @return canExecute Whether sentiment conditions are met
    /// @return currentScore The current sentiment score
    /// @return reason Human-readable reason if not executable
    function checkProposal(uint256 proposalId) external view returns (
        bool canExecute,
        uint8 currentScore,
        string memory reason
    ) {
        if (proposalId >= proposals.length) return (false, 0, "Proposal not found");
        Proposal storage p = proposals[proposalId];
        if (p.executed) return (false, 0, "Already executed");
        if (p.cancelled) return (false, 0, "Cancelled");

        SentimentOracle.SentimentData memory sentiment = oracle.getSentiment(p.project);
        currentScore = sentiment.score;

        if (block.timestamp - sentiment.timestamp > freshnessWindow) {
            return (false, currentScore, "Sentiment data is stale");
        }

        if (currentScore < sentimentThreshold) {
            return (false, currentScore, "Sentiment below threshold");
        }

        return (true, currentScore, "Ready to execute");
    }

    function getProposalCount() external view returns (uint256) {
        return proposals.length;
    }
}
