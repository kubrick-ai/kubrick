#!/usr/bin/env node
import { resolve } from "path";
import color from "picocolors";
import * as p from "@clack/prompts";
import { deployCommand } from "./commands/deploy.js";
import { banner } from "./theme/index.js";
import { destroyCommand } from "./commands/destroy.js";

const main = async () => {
  console.clear();
  console.log(banner);

  p.updateSettings({
    aliases: {
      k: "up",
      j: "down",
      h: "left",
      l: "right",
    },
  });

  const args = process.argv.slice(2);
  const command = args[0];

  // Show help when no command is passed or help is requested
  if (!command || args.includes("--help") || args.includes("-h")) {
    console.log(`
${color.cyan(color.bold("Kubrick CLI"))} - Deploy Kubrick infrastructure with Lambda packages and Terraform

${color.yellow("Usage:")}
  ${color.green("kubrick")} ${color.blue("<command>")} ${color.gray("[options]")}

${color.yellow("Commands:")}
  ${color.green("deploy")}        Deploy new or existing Kubrick infrastructure
  ${color.green("destroy")}       Destroy existing Kubrick infrastructure

${color.yellow("Options:")}
  ${color.gray("--help, -h")}    Show this help message

${color.yellow("Examples:")}
  ${color.green("kubrick deploy")}    Deploy with interactive prompts
  ${color.green("kubrick destroy")}   Destroy with interactive prompts
  ${color.green("kubrick --help")}    Show this help message
`);
    process.exit(0);
  }

  const rootDir = resolve(process.cwd(), "..");

  // Handle commands
  switch (command) {
    case "deploy":
      await deployCommand(rootDir);
      break;
    case "destroy":
      await destroyCommand(rootDir);
      break;
    default:
      console.error(`Unknown command: ${command}`);
      console.log(`Run 'kubrick --help' for available commands.`);
      process.exit(1);
  }
};

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
