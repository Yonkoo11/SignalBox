// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {SentimentOracle} from "../src/SentimentOracle.sol";

/// @notice One-time script to populate Tenderly VNet with sentiment data
contract PopulateTenderlyScript is Script {
    function run() public {
        address oracleAddr = vm.envAddress("ORACLE_ADDRESS");
        SentimentOracle oracle = SentimentOracle(oracleAddr);

        address owner = oracle.owner();
        address originalForwarder = oracle.getForwarderAddress();

        vm.startBroadcast();

        // Temporarily set forwarder to owner so we can call onReport
        oracle.setForwarderAddress(owner);

        // Empty metadata (no workflow validation configured)
        bytes memory metadata = new bytes(62);

        // Chainlink: score 82, 8 mentions, 5+/2-/1~
        oracle.onReport(
            metadata,
            abi.encode("chainlink", uint8(82), uint32(8), uint32(5), uint32(2), uint32(1), "Community sentiment for Chainlink is strongly positive at 82/100. CCIP adoption and CRE launch generating excitement.")
        );

        // Aave: score 78, 6 mentions, 4+/1-/1~
        oracle.onReport(
            metadata,
            abi.encode("aave", uint8(78), uint32(6), uint32(4), uint32(1), uint32(1), "Aave maintains strong sentiment at 78/100. GHO stablecoin launch and V3 efficiency mode well received.")
        );

        // Base: score 71, 6 mentions, 4+/2-/0~
        oracle.onReport(
            metadata,
            abi.encode("base", uint8(71), uint32(6), uint32(4), uint32(2), uint32(0), "Base shows growing positive sentiment at 71/100. Low fees and Coinbase integration driving adoption.")
        );

        // Uniswap: score 65, 6 mentions, 2+/2-/2~
        oracle.onReport(
            metadata,
            abi.encode("uniswap", uint8(65), uint32(6), uint32(2), uint32(2), uint32(2), "Sentiment for Uniswap is moderate-positive at 65/100. V4 hooks generating interest but fee switch debate ongoing.")
        );

        // Arbitrum: score 58, 6 mentions, 3+/2-/1~
        oracle.onReport(
            metadata,
            abi.encode("arbitrum", uint8(58), uint32(6), uint32(3), uint32(2), uint32(1), "Arbitrum sentiment is mixed-positive at 58/100. Stylus and BOLD upgrades positive but sequencer centralization concerns persist.")
        );

        // Restore original forwarder
        oracle.setForwarderAddress(originalForwarder);

        vm.stopBroadcast();

        console.log("Populated 5 projects on Tenderly VNet");
        console.log("Forwarder restored to:", originalForwarder);
    }
}
