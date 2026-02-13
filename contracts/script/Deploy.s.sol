// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {SentimentOracle} from "../src/SentimentOracle.sol";

contract DeployScript is Script {
    function run() public {
        address forwarder = vm.envAddress("FORWARDER_ADDRESS");

        vm.startBroadcast();
        SentimentOracle oracle = new SentimentOracle(forwarder);
        vm.stopBroadcast();

        console.log("SentimentOracle deployed at:", address(oracle));
        console.log("Owner:", oracle.owner());
        console.log("Forwarder:", oracle.getForwarderAddress());
    }
}
