// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {SentimentSentinel} from "../src/SentimentSentinel.sol";

contract DeploySentinelScript is Script {
    function run() public {
        address oracle = vm.envAddress("ORACLE_ADDRESS");
        address gate = vm.envAddress("GATE_ADDRESS");

        vm.startBroadcast();
        SentimentSentinel sentinel = new SentimentSentinel(
            oracle,
            gate,
            7200,   // staleness: data older than 2 hours triggers alert
            3600    // cooldown: max 1 alert per hour
        );
        vm.stopBroadcast();

        console.log("SentimentSentinel deployed at:", address(sentinel));
        console.log("Oracle:", address(sentinel.oracle()));
        console.log("Gate:", address(sentinel.gate()));
        console.log("Staleness threshold:", sentinel.stalenessThreshold());
    }
}
