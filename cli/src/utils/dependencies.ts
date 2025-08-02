import * as p from "@clack/prompts";
import color from "picocolors";
import { commandExists } from "./shell.js";

const REQUIRED_DEPENDENCIES = [
  { name: "terraform", description: "Terraform CLI" },
  { name: "aws", description: "AWS CLI" },
  { name: "python3", description: "Python 3" },
  { name: "uv", description: "UV package manager" },
];

export const checkDependencies = async (): Promise<void> => {
  p.log.step("Checking dependencies...");

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
      "❌ Dependency Check Failed",
    );
    p.cancel("Cannot proceed without required dependencies");
    process.exit(1);
  }

  p.log.success("✓ All required dependencies are installed");
};
