import { setTimeout } from "node:timers/promises";
import * as p from "@clack/prompts";
import color from "picocolors";
import { commandExists } from "./shell.js";
import { symbols } from "../theme/index.js";

const REQUIRED_DEPENDENCIES = [
  { name: "terraform", description: "Terraform CLI" },
  { name: "aws", description: "AWS CLI" },
  { name: "python3", description: "Python 3" },
  { name: "uv", description: "UV package manager" },
];

export const checkDependencies = async (): Promise<void> => {
  const s = p.spinner();
  s.start(`${symbols.process} Checking dependencies...`);

  // add delay for visibility
  await setTimeout(1000);

  const missingDeps: string[] = [];

  for (const dep of REQUIRED_DEPENDENCIES) {
    const exists = await commandExists(dep.name);
    if (!exists) {
      missingDeps.push(dep.description);
    }
  }

  if (missingDeps.length > 0) {
    p.note(
      `Missing dependencies:
${missingDeps.map((dep) => `• ${color.red(dep)}`).join("\n")}\n
Please install the missing dependencies and try again.
See README.md for installation instructions.`,
      `${symbols.error} Dependency Check Failed`,
    );
    p.cancel(`${symbols.error} Cannot proceed without required dependencies`);
    process.exit(1);
  }

  s.stop(`${symbols.success} All required dependencies are installed`);
};
