// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {SentimentOracle} from "../src/SentimentOracle.sol";
import {SentimentGate} from "../src/SentimentGate.sol";

contract SentimentGateTest is Test {
    SentimentOracle oracle;
    SentimentGate gate;
    address owner = address(this);

    function setUp() public {
        oracle = new SentimentOracle(address(0xF00D));
        oracle.setForwarderAddress(address(0)); // disable for testing
        gate = new SentimentGate(
            address(oracle),
            50,    // threshold: sentiment must be >= 50
            3600   // freshness: data must be < 1 hour old
        );
    }

    function _submitSentiment(string memory project, uint8 score) internal {
        bytes memory report = abi.encode(
            project, score, uint32(100), uint32(60), uint32(20), uint32(20), "test summary"
        );
        oracle.onReport("", report);
    }

    function test_createProposal() public {
        uint256 id = gate.createProposal(
            "chainlink",
            "Upgrade oracle feed frequency",
            address(0),
            ""
        );
        assertEq(id, 0);
        assertEq(gate.getProposalCount(), 1);
    }

    function test_executeProposal_sentimentAboveThreshold() public {
        _submitSentiment("chainlink", 75);

        gate.createProposal("chainlink", "Test proposal", address(0), "");
        gate.executeProposal(0);

        (, , , , , bool executed, ) = gate.proposals(0);
        assertTrue(executed);
    }

    function test_executeProposal_revertsBelowThreshold() public {
        _submitSentiment("chainlink", 30); // below 50 threshold

        gate.createProposal("chainlink", "Risky proposal", address(0), "");

        vm.expectRevert(
            abi.encodeWithSelector(SentimentGate.SentimentTooLow.selector, 30, 50)
        );
        gate.executeProposal(0);
    }

    function test_executeProposal_revertsOnStaleData() public {
        _submitSentiment("chainlink", 80);

        gate.createProposal("chainlink", "Delayed proposal", address(0), "");

        // Warp 2 hours into the future (beyond 1 hour freshness window)
        vm.warp(block.timestamp + 7200);

        vm.expectRevert(); // SentimentDataStale
        gate.executeProposal(0);
    }

    function test_checkProposal_ready() public {
        _submitSentiment("chainlink", 80);
        gate.createProposal("chainlink", "Good proposal", address(0), "");

        (bool canExecute, uint8 score, string memory reason) = gate.checkProposal(0);
        assertTrue(canExecute);
        assertEq(score, 80);
        assertEq(reason, "Ready to execute");
    }

    function test_checkProposal_belowThreshold() public {
        _submitSentiment("chainlink", 40);
        gate.createProposal("chainlink", "Bad timing", address(0), "");

        (bool canExecute, uint8 score, string memory reason) = gate.checkProposal(0);
        assertFalse(canExecute);
        assertEq(score, 40);
        assertEq(reason, "Sentiment below threshold");
    }

    function test_cancelProposal() public {
        gate.createProposal("chainlink", "Cancel me", address(0), "");
        gate.cancelProposal(0);

        (bool canExecute, , string memory reason) = gate.checkProposal(0);
        assertFalse(canExecute);
        assertEq(reason, "Cancelled");
    }

    function test_setThreshold() public {
        assertEq(gate.sentimentThreshold(), 50);
        gate.setThreshold(70);
        assertEq(gate.sentimentThreshold(), 70);
    }

    function test_executeProposal_withTargetCall() public {
        // Deploy a simple counter to test actual execution
        Counter counter = new Counter();
        assertEq(counter.count(), 0);

        _submitSentiment("chainlink", 80);

        gate.createProposal(
            "chainlink",
            "Increment counter",
            address(counter),
            abi.encodeWithSelector(Counter.increment.selector)
        );
        gate.executeProposal(0);

        assertEq(counter.count(), 1);
    }

    function test_executeProposal_revertsOnDoubleExecution() public {
        _submitSentiment("chainlink", 80);
        gate.createProposal("chainlink", "Once only", address(0), "");
        gate.executeProposal(0);

        vm.expectRevert(SentimentGate.ProposalAlreadyExecuted.selector);
        gate.executeProposal(0);
    }

    function test_onlyOwner() public {
        address notOwner = address(0xBEEF);
        vm.prank(notOwner);
        vm.expectRevert(SentimentGate.OnlyOwner.selector);
        gate.createProposal("chainlink", "Unauthorized", address(0), "");
    }
}

/// @dev Simple contract for testing executeProposal with target calls
contract Counter {
    uint256 public count;
    function increment() external { count++; }
}
