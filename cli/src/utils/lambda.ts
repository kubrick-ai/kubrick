import * as p from "@clack/prompts";
import color from "picocolors";
import { existsSync, readdirSync, statSync } from "fs";
import { resolve, join, dirname } from "path";
import { runCommand } from "./shell.js";
import { symbols } from "../theme/index.js";

const findLambdaPackageDirectories = (rootDir: string): string[] => {
  const lambdaDir = join(rootDir, "lambda");

  if (!existsSync(lambdaDir)) {
    return [];
  }

  const directories: string[] = [];

  const searchRecursively = (dir: string): void => {
    try {
      const items = readdirSync(dir);

      for (const item of items) {
        const fullPath = join(dir, item);
        const stat = statSync(fullPath);

        if (stat.isDirectory()) {
          searchRecursively(fullPath);
        } else if (item === "pyproject.toml") {
          directories.push(dirname(fullPath));
        }
      }
    } catch (error) {
      // Skip directories we can't read
    }
  };

  searchRecursively(lambdaDir);
  return directories;
};

export const buildLambdas = async (rootDir: string): Promise<void> => {
  // Find all directories with pyproject.toml files in the lambda directory
  const packageDirectories = findLambdaPackageDirectories(rootDir);

  if (packageDirectories.length === 0) {
    p.log.warn("No pyproject.toml files found in lambda directory");
    return;
  }

  const buildScript = resolve(rootDir, "lambda/build-package.sh");

  const tasks = packageDirectories.map((packageDir) => {
    const packageName = color.blue(packageDir.replace(rootDir + "/", ""));
    return {
      title: `Building ${packageName}`,
      task: async () => {
        const result = await runCommand("bash", [buildScript], {
          cwd: packageDir,
        });

        if (!result.success) {
          throw new Error(result.stderr);
        }

        return `${packageName} built successfully`;
      },
    };
  });

  await p.tasks(tasks);
};
