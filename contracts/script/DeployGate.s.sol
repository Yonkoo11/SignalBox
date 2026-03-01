// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {SentimentGate} from "../src/SentimentGate.sol";

contract DeployGateScript is Script {
    function run() public {
        address oracle = vm.envAddress("ORACLE_ADDRESS");

        vm.startBroadcast();
        SentimentGate gate = new SentimentGate(
            oracle,
            50,    // threshold: sentiment must be >= 50 to execute
            7200   // freshness: data must be < 2 hours old
        );
        vm.stopBroadcast();

        console.log("SentimentGate deployed at:", address(gate));
        console.log("Oracle:", address(gate.oracle()));
        console.log("Threshold:", gate.sentimentThreshold());
        console.log("Owner:", gate.owner());
    }
}
