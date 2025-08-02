import * as p from "@clack/prompts";
import { existsSync } from "fs";
import { resolve } from "path";
import { runCommand } from "./shell.js";

export const buildLambdas = async (rootDir: string): Promise<void> => {
  const buildScript = resolve(rootDir, "build-lambda-packages.sh");

  if (!existsSync(buildScript)) {
    p.cancel("build-lambda-packages.sh not found in project root");
    process.exit(1);
  }

  const s = p.spinner();
  s.start("🏗️ Building Lambda packages...");

  const result = await runCommand("bash", [buildScript], { cwd: rootDir });

  if (!result.success) {
    s.stop("❌ Lambda build failed");
    p.cancel(`Lambda build failed: ${result.stderr}`);
    process.exit(1);
  }

  s.stop("✅ Lambda packages built successfully");
};
