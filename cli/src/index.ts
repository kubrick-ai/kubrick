#!/usr/bin/env node
import path from "node:path";
import { findUp, pathExists } from "find-up";
import * as p from "@clack/prompts";
import { banner } from "./theme/index.js";
import { helpCommand } from "./commands/help.js";
import { deployCommand } from "./commands/deploy.js";
import { destroyCommand } from "./commands/destroy.js";

const main = async () => {
  console.clear();
  console.log(banner);

  const rootDir =
    (await findUp(
      async (dir) => {
        const hasGit = await pathExists(path.join(dir, ".git"));
        const hasTerraform = await pathExists(path.join(dir, "terraform"));
        const hasPlayground = await pathExists(path.join(dir, "playground"));
        const hasLambdaDir = await pathExists(path.join(dir, "lambda"));
        if (hasGit && hasTerraform && hasPlayground && hasLambdaDir) return dir;
      },
      { type: "directory" },
    )) ?? path.resolve(process.cwd());

  const args = process.argv.slice(2);
  const command = args[0];

  p.updateSettings({
    aliases: {
      k: "up",
      j: "down",
      h: "left",
      l: "right",
    },
  });

  // basic single command handling for now
  switch (command) {
    case undefined:
    case "-h":
    case "--help":
      helpCommand();
      break;
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
