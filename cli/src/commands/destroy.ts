import * as p from "@clack/prompts";
import color from "picocolors";
import { resolve } from "path";
import { existsSync } from "fs";
import type { OperationConfig } from "../types/index.js";
import { handleCancel } from "../utils/misc.js";
import { checkDependencies } from "../utils/dependencies.js";
import { symbols } from "../theme/index.js";
import {
  getAWSProfiles,
  getAWSRegions,
  validateAWSCredentials,
  checkAWSPermissions,
} from "../utils/aws.js";
import { destroyTerraform } from "../utils/terraform.js";

export const destroyCommand = async (rootDir: string): Promise<void> => {
  p.intro(`${color.bgBlue(color.white(" Kubrick Destroy "))}`);

  // Find project root directory
  const terraformDir = resolve(rootDir, "terraform");

  if (!existsSync(terraformDir)) {
    p.cancel(
      `${symbols.error} Terraform directory not found. Please run from project root.`,
    );
    process.exit(1);
  }

  try {
    await checkDependencies();

    const availableAWSProfiles = await getAWSProfiles();
    const availableAWSRegions = await getAWSRegions();
    const config: OperationConfig = await p.group(
      {
        profile: () =>
          p.select({
            message: "Select the AWS Profile to use for this operation",
            options: availableAWSProfiles.map((profile) => ({
              value: profile,
              label: profile,
            })),
          }),
        region: () =>
          p.select({
            message: "Select the AWS Region your infrastructure is deployed in",
            options: availableAWSRegions.map((region) => ({
              value: region,
              label: region,
            })),
          }),
        skipAuthCheck: () =>
          p.confirm({
            message: "Skip AWS authentication check?",
            initialValue: false,
          }),
      },
      {
        onCancel: () => {
          p.cancel(`${symbols.error} Destroy operation cancelled.`);
          process.exit(0);
        },
      },
    );

    if (!config.skipAuthCheck) {
      await validateAWSCredentials(config.profile, config.region);
      await checkAWSPermissions(config.profile, config.region);
    } else {
      p.log.warn(`${symbols.warning} Skipping AWS authentication check`);
    }

    // TODO: Add confirmation step

    const outputs = await destroyTerraform(
      terraformDir,
      config.profile,
      config.region,
    );

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
