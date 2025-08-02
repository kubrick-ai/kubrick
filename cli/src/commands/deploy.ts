import * as p from "@clack/prompts";
import color from "picocolors";
import { resolve } from "path";
import { existsSync } from "fs";
import type { DeployConfig } from "../types/index.js";
import { handleCancel } from "../utils/misc.js";
import { checkDependencies } from "../utils/dependencies.js";
import { symbols } from "../theme/index.js";
import {
  getAWSProfiles,
  getAWSRegions,
  validateAWSCredentials,
  checkAWSPermissions,
} from "../utils/aws.js";
import { buildLambdas } from "../utils/lambda.js";
import {
  checkTerraformVars,
  getSecretConfig,
  initializeTerraform,
  deployTerraform,
} from "../utils/terraform.js";

export const deployCommand = async (rootDir: string): Promise<void> => {
  p.intro(`${color.bgBlue(color.white(" Kubrick Deployment "))}`);

  // Find project root directory
  const terraformDir = resolve(rootDir, "terraform");

  if (!existsSync(terraformDir)) {
    p.cancel(`${symbols.error} Terraform directory not found. Please run from project root.`);
    process.exit(1);
  }

  try {
    await checkDependencies();

    const availableAWSProfiles = await getAWSProfiles();
    const availableAWSRegions = await getAWSRegions();
    const deployConfig: DeployConfig = await p.group(
      {
        profile: () =>
          p.select({
            message: "Select the AWS Profile to use for this deployment",
            options: availableAWSProfiles.map((profile) => ({
              value: profile,
              label: profile,
            })),
          }),
        region: () =>
          p.select({
            message: "Select an AWS Region to deploy in",
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
          p.cancel(`${symbols.error} Deployment cancelled.`);
          process.exit(0);
        },
      },
    );

    if (!deployConfig.skipAuthCheck) {
      await validateAWSCredentials(deployConfig.profile, deployConfig.region);
      await checkAWSPermissions(deployConfig.profile, deployConfig.region);
    } else {
      p.log.warn(`${symbols.warning} Skipping AWS authentication check`);
    }

    const shouldBuildLambdas = handleCancel(
      await p.confirm({
        message: "Build Lambda packages? (Required for first deployment)",
        initialValue: true,
      }),
    );

    if (shouldBuildLambdas) {
      await buildLambdas(rootDir);
    } else {
      p.log.warn(`${symbols.warning} Skipping Lambda package build`);
    }

    await checkTerraformVars(rootDir);
    await initializeTerraform(terraformDir);

    const secretConfig = await getSecretConfig();

    const outputs = await deployTerraform(
      terraformDir,
      secretConfig,
      deployConfig.profile,
      deployConfig.region,
    );

    p.log.success(
      `${symbols.success} ${color.green("Kubrick deployment completed successfully!")}`,
    );

    const showOutput = handleCancel(
      await p.confirm({
        message: "Show terraform outputs?",
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
