// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test, Vm} from "forge-std/Test.sol";
import {SentimentOracle} from "../src/SentimentOracle.sol";

contract SentimentOracleTest is Test {
    SentimentOracle oracle;
    address deployer = address(this);
    address forwarder = address(0xF00D);

    function setUp() public {
        oracle = new SentimentOracle(forwarder);
        // Disable forwarder check for testing so we can call onReport directly
        oracle.setForwarderAddress(address(0));
    }

    function _buildReport(
        string memory project,
        uint8 score,
        uint32 total,
        uint32 pos,
        uint32 neg,
        uint32 neutral,
        string memory summary
    ) internal pure returns (bytes memory) {
        return abi.encode(project, score, total, pos, neg, neutral, summary);
    }

    function _callReport(bytes memory report) internal {
        // Empty metadata for tests (no workflow validation)
        oracle.onReport("", report);
    }

    function test_processReport() public {
        bytes memory report = _buildReport("uniswap", 75, 100, 60, 20, 20, "Mostly positive");
        _callReport(report);

        SentimentOracle.SentimentData memory data = oracle.getSentiment("uniswap");
        assertEq(data.score, 75);
        assertEq(data.totalMentions, 100);
        assertEq(data.positive, 60);
        assertEq(data.negative, 20);
        assertEq(data.neutral, 20);
    }

    function test_revertScoreOver100() public {
        bytes memory report = _buildReport("uniswap", 101, 100, 60, 20, 20, "test");
        vm.expectRevert("Score must be 0-100");
        _callReport(report);
    }

    function test_trackedProjects() public {
        _callReport(_buildReport("uniswap", 70, 50, 30, 10, 10, "ok"));
        _callReport(_buildReport("aave", 80, 30, 25, 3, 2, "good"));

        string[] memory projects = oracle.getTrackedProjects();
        assertEq(projects.length, 2);
        assertTrue(oracle.isTracked("uniswap"));
        assertTrue(oracle.isTracked("aave"));
    }

    function test_history() public {
        _callReport(_buildReport("uniswap", 60, 40, 20, 10, 10, "meh"));
        _callReport(_buildReport("uniswap", 70, 50, 30, 10, 10, "better"));
        _callReport(_buildReport("uniswap", 80, 60, 45, 5, 10, "great"));

        assertEq(oracle.getHistoryLength("uniswap"), 3);

        SentimentOracle.SentimentData[] memory last2 = oracle.getHistory("uniswap", 2);
        assertEq(last2.length, 2);
        assertEq(last2[0].score, 70);
        assertEq(last2[1].score, 80);
    }

    function test_riskAlert_emitsOnLargeDrop() public {
        // First report: score 80
        _callReport(_buildReport("uniswap", 80, 50, 30, 10, 10, "good"));
        // Second report: score 60 (drop of 20, > RISK_THRESHOLD of 15)
        vm.expectEmit(false, false, false, false);
        emit SentimentOracle.RiskAlert("uniswap", 80, 60, 20, block.timestamp);
        _callReport(_buildReport("uniswap", 60, 50, 20, 20, 10, "dropping"));
    }

    function test_riskAlert_noEmitOnSmallDrop() public {
        // First report: score 80
        _callReport(_buildReport("uniswap", 80, 50, 30, 10, 10, "good"));
        // Second report: score 70 (drop of 10, < RISK_THRESHOLD of 15)
        vm.recordLogs();
        _callReport(_buildReport("uniswap", 70, 50, 25, 15, 10, "slight dip"));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        // Should have SentimentUpdated but NOT RiskAlert
        for (uint i = 0; i < logs.length; i++) {
            assertTrue(
                logs[i].topics[0] != keccak256("RiskAlert(string,uint8,uint8,uint8,uint256)"),
                "RiskAlert should not emit on small drop"
            );
        }
    }

    function test_riskAlert_noEmitOnScoreIncrease() public {
        _callReport(_buildReport("uniswap", 60, 50, 20, 20, 10, "meh"));
        vm.recordLogs();
        _callReport(_buildReport("uniswap", 80, 50, 35, 5, 10, "recovery"));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        for (uint i = 0; i < logs.length; i++) {
            assertTrue(
                logs[i].topics[0] != keccak256("RiskAlert(string,uint8,uint8,uint8,uint256)"),
                "RiskAlert should not emit on score increase"
            );
        }
    }

    function test_forwarderEnforced() public {
        // Deploy a fresh oracle with forwarder check enabled
        SentimentOracle strict = new SentimentOracle(forwarder);

        bytes memory report = _buildReport("test", 50, 10, 5, 3, 2, "test");
        // Should revert because we're not the forwarder
        vm.expectRevert();
        strict.onReport("", report);
    }
}
