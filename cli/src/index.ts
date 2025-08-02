// #!/usr/bin/env node
import * as p from "@clack/prompts";
import { deployCommand } from "./commands/deploy.js";

const main = async () => {
  console.clear();

  p.updateSettings({
    aliases: {
      k: "up",
      j: "down",
      h: "left",
      l: "right",
    },
  });

  const args = process.argv.slice(2);

  // For now, we only have the deploy command
  // In the future, we can add command parsing here
  if (args.includes("--help") || args.includes("-h")) {
    console.log(`
Kubrick CLI - Deploy Kubrick infrastructure with Lambda packages and Terraform

Usage:
  kubrick [options]

Options:
  --help, -h    Show this help message

Examples:
  kubrick       Deploy with interactive prompts
`);
    process.exit(0);
  }

  await deployCommand();
};

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
