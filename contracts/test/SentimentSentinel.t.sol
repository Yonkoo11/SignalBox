// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {SentimentOracle} from "../src/SentimentOracle.sol";
import {SentimentGate} from "../src/SentimentGate.sol";
import {SentimentSentinel} from "../src/SentimentSentinel.sol";

contract SentimentSentinelTest is Test {
    SentimentOracle oracle;
    SentimentGate gate;
    SentimentSentinel sentinel;

    function setUp() public {
        oracle = new SentimentOracle(address(0xF00D));
        oracle.setForwarderAddress(address(0)); // disable forwarder for testing
        gate = new SentimentGate(address(oracle), 50, 3600);
        sentinel = new SentimentSentinel(
            address(oracle),
            address(gate),
            7200,   // 2 hours staleness threshold
            3600    // 1 hour cooldown
        );
    }

    function _submitSentiment(string memory project, uint8 score) internal {
        bytes memory report = abi.encode(
            project, score, uint32(100), uint32(60), uint32(20), uint32(20), "test summary"
        );
        oracle.onReport("", report);
    }

    function test_constructor() public view {
        assertEq(address(sentinel.oracle()), address(oracle));
        assertEq(address(sentinel.gate()), address(gate));
        assertEq(sentinel.stalenessThreshold(), 7200);
        assertEq(sentinel.alertCooldown(), 3600);
        assertEq(sentinel.alertCount(), 0);
    }

    function test_checkUpkeep_noProjects() public {
        (bool needed, ) = sentinel.checkUpkeep("");
        assertFalse(needed);
    }

    function test_checkUpkeep_freshData() public {
        _submitSentiment("chainlink", 80);
        (bool needed, ) = sentinel.checkUpkeep("");
        assertFalse(needed); // data is fresh, no upkeep needed
    }

    function test_checkUpkeep_staleData() public {
        _submitSentiment("chainlink", 80);
        vm.warp(block.timestamp + 7201); // just past staleness threshold
        (bool needed, bytes memory data) = sentinel.checkUpkeep("");
        assertTrue(needed);
        uint256 idx = abi.decode(data, (uint256));
        assertEq(idx, 0); // first project
    }

    function test_performUpkeep_emitsAlert() public {
        _submitSentiment("chainlink", 80);
        vm.warp(block.timestamp + 7201);

        vm.expectEmit(false, false, false, false);
        emit SentimentSentinel.StaleDataAlert("chainlink", 7201, 7200, block.timestamp);

        sentinel.performUpkeep(abi.encode(uint256(0)));
        assertEq(sentinel.alertCount(), 1);
    }

    function test_performUpkeep_respectsCooldown() public {
        _submitSentiment("chainlink", 80);
        vm.warp(block.timestamp + 7201);

        sentinel.performUpkeep(abi.encode(uint256(0)));

        // Try again immediately - should fail due to cooldown
        vm.expectRevert("Alert cooldown active");
        sentinel.performUpkeep(abi.encode(uint256(0)));
    }

    function test_performUpkeep_afterCooldown() public {
        _submitSentiment("chainlink", 80);
        vm.warp(block.timestamp + 7201);

        sentinel.performUpkeep(abi.encode(uint256(0)));
        assertEq(sentinel.alertCount(), 1);

        // Wait for cooldown to pass
        vm.warp(block.timestamp + 3601);

        sentinel.performUpkeep(abi.encode(uint256(0)));
        assertEq(sentinel.alertCount(), 2);
    }

    function test_performUpkeep_revertsOnFreshData() public {
        // Warp to a reasonable timestamp first (past initial cooldown)
        vm.warp(10000);
        _submitSentiment("chainlink", 80);
        // Data just submitted - well within 7200s staleness window

        vm.expectRevert("Data is fresh");
        sentinel.performUpkeep(abi.encode(uint256(0)));
    }

    function test_performUpkeep_revertsOnInvalidIndex() public {
        _submitSentiment("chainlink", 80);
        vm.warp(block.timestamp + 7201);

        vm.expectRevert("Invalid project index");
        sentinel.performUpkeep(abi.encode(uint256(99)));
    }

    function test_checkUpkeep_multipleProjects_firstStale() public {
        _submitSentiment("chainlink", 80);
        vm.warp(block.timestamp + 100); // small gap
        _submitSentiment("aave", 75);
        vm.warp(block.timestamp + 7200); // chainlink is stale, aave might be too

        (bool needed, bytes memory data) = sentinel.checkUpkeep("");
        assertTrue(needed);
        uint256 idx = abi.decode(data, (uint256));
        assertEq(idx, 0); // reports first stale project found
    }

    function test_setConfig() public {
        sentinel.setConfig(14400, 7200);
        assertEq(sentinel.stalenessThreshold(), 14400);
        assertEq(sentinel.alertCooldown(), 7200);
    }

    function test_setConfig_onlyOwner() public {
        vm.prank(address(0xBEEF));
        vm.expectRevert(SentimentSentinel.OnlyOwner.selector);
        sentinel.setConfig(14400, 7200);
    }
}
