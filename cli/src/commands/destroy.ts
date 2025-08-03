import * as p from "@clack/prompts";
import color from "picocolors";
import { resolve } from "path";
import { existsSync } from "fs";
import { handleCancel } from "../utils/misc.js";
import { checkDependencies } from "../utils/dependencies.js";
import { symbols } from "../theme/index.js";
import { destroyTerraform } from "../utils/terraform.js";

export const destroyCommand = async (rootDir: string): Promise<void> => {
  p.intro(`${color.bgBlue(color.white(" Kubrick Destroy "))}`);

  // Find project root directory
  const terraformDir = resolve(rootDir, "terraform");

  if (!existsSync(terraformDir)) {
    p.cancel(
      `${symbols.error} Terraform directory not found. Please run from within the Kubrick project.`,
    );
    process.exit(1);
  }

  try {
    await checkDependencies();

    const confirmDeployStep = handleCancel(
      await p.confirm({
        message:
          "Are you sure you want to destroy the deployed infrastructure?",
        initialValue: false,
      }),
    );

    if (!confirmDeployStep) {
      p.cancel(`Destroy operation cancelled by user.`);
      process.exit(1);
    }

    const outputs = await destroyTerraform(terraformDir);

    p.log.success(
      `${symbols.success} ${color.green("Kubrick infrastructure destroyed successfully!")}`,
    );

    const showOutput = handleCancel(
      await p.confirm({
        message: "Show outputs?",
      }),
    );
    if (showOutput) {
      p.note(outputs, "Output");
    }

    p.outro("Exiting...");
  } catch (error) {
    if (error instanceof Error) {
      p.cancel(`${symbols.error} Deployment failed: ${error.message}`);
    } else {
      p.cancel(`${symbols.error} Deployment failed with unknown error`);
    }
    process.exit(1);
  }
};
