// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {SentimentOracle} from "./SentimentOracle.sol";
import {SentimentGate} from "./SentimentGate.sol";

/// @title AutomationCompatibleInterface - Chainlink Automation
/// @dev Inline to avoid pulling in @chainlink/contracts dependency
interface AutomationCompatibleInterface {
    function checkUpkeep(bytes calldata checkData) external returns (bool upkeepNeeded, bytes memory performData);
    function performUpkeep(bytes calldata performData) external;
}

/// @title SentimentSentinel - Chainlink Automation for oracle health monitoring
/// @notice Monitors SentimentOracle data freshness and emits alerts when stale.
///         Demonstrates Chainlink Automation as a second Chainlink service alongside CRE.
/// @dev Register as a Custom Logic upkeep at automation.chain.link
contract SentimentSentinel is AutomationCompatibleInterface {
    SentimentOracle public immutable oracle;
    SentimentGate public immutable gate;
    address public owner;

    uint256 public stalenessThreshold; // seconds before data is considered stale
    uint256 public lastAlertTimestamp;  // when the last alert was emitted
    uint256 public alertCooldown;      // min seconds between alerts

    uint256 public alertCount;         // total alerts emitted

    event StaleDataAlert(
        string project,
        uint256 dataAge,
        uint256 threshold,
        uint256 timestamp
    );
    event StalenessConfigUpdated(uint256 threshold, uint256 cooldown);

    error OnlyOwner();

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    constructor(
        address _oracle,
        address _gate,
        uint256 _stalenessThreshold,
        uint256 _alertCooldown
    ) {
        oracle = SentimentOracle(_oracle);
        gate = SentimentGate(_gate);
        owner = msg.sender;
        stalenessThreshold = _stalenessThreshold;
        alertCooldown = _alertCooldown;
    }

    /// @notice Called off-chain by Chainlink Automation nodes every block
    /// @dev Checks if any tracked project has stale sentiment data
    function checkUpkeep(bytes calldata)
        external
        view
        override
        returns (bool upkeepNeeded, bytes memory performData)
    {
        // Respect cooldown
        if (block.timestamp < lastAlertTimestamp + alertCooldown) {
            return (false, "");
        }

        string[] memory projects = oracle.getTrackedProjects();
        for (uint256 i = 0; i < projects.length; i++) {
            SentimentOracle.SentimentData memory data = oracle.getSentiment(projects[i]);
            if (data.timestamp > 0) {
                uint256 age = block.timestamp - data.timestamp;
                if (age > stalenessThreshold) {
                    return (true, abi.encode(i));
                }
            }
        }

        return (false, "");
    }

    /// @notice Called on-chain by Chainlink Automation when checkUpkeep returns true
    /// @dev Re-validates staleness before emitting alert (Chainlink best practice)
    function performUpkeep(bytes calldata performData) external override {
        uint256 projectIndex = abi.decode(performData, (uint256));

        // Re-validate cooldown
        require(
            block.timestamp >= lastAlertTimestamp + alertCooldown,
            "Alert cooldown active"
        );

        string[] memory projects = oracle.getTrackedProjects();
        require(projectIndex < projects.length, "Invalid project index");

        SentimentOracle.SentimentData memory data = oracle.getSentiment(projects[projectIndex]);
        uint256 age = block.timestamp - data.timestamp;

        // Re-validate staleness
        require(age > stalenessThreshold, "Data is fresh");

        lastAlertTimestamp = block.timestamp;
        alertCount++;

        emit StaleDataAlert(
            projects[projectIndex],
            age,
            stalenessThreshold,
            block.timestamp
        );
    }

    /// @notice Update staleness configuration
    function setConfig(uint256 _threshold, uint256 _cooldown) external onlyOwner {
        stalenessThreshold = _threshold;
        alertCooldown = _cooldown;
        emit StalenessConfigUpdated(_threshold, _cooldown);
    }
}
