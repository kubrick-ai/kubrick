import * as p from "@clack/prompts";
import color from "picocolors";
import { resolve } from "path";
import { existsSync } from "fs";
import { handleCancel, extractOutputs } from "../utils/misc.js";
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
  determineSecretName,
  importSecret,
  parseTerraformVars,
  writeTerraformVars,
  initializeTerraform,
  deployTerraform,
  tfvarsFileExists,
} from "../utils/terraform.js";
import type { TFVarsConfig, TFVarsConfigCore } from "../types/index.js";

export const promptTfVars = async () => {
  const availableAWSProfiles = await getAWSProfiles();
  const availableAWSRegions = await getAWSRegions();

  const tfvarsConfigCore: TFVarsConfigCore = await p.group(
    {
      aws_profile: () =>
        p.select({
          message: "Select the AWS Profile to use for this deployment",
          options: availableAWSProfiles.map((profile) => ({
            value: profile,
            label: profile,
          })),
        }),
      aws_region: () =>
        p.select({
          message: "Select an AWS Region to deploy in",
          options: availableAWSRegions.map((region) => ({
            value: region,
            label: region,
          })),
        }),
      twelvelabs_api_key: () =>
        p.password({
          message: "Enter your TwelveLabs API key",
          validate: (value) => {
            if (!value?.trim()) return "TwelveLabs API key is required";
          },
        }),
      db_username: () =>
        p.text({
          message: "Enter a username for your database ",
          placeholder: "postgres",
          defaultValue: "postgres",
        }),
      db_password: () =>
        p.password({
          message: "Enter a password for your database",
          validate: (value) => {
            if (!value?.trim()) return "Database password is required";
            if (value.length < 8)
              return "Password must be at least 8 characters";
          },
        }),
    },
    {
      onCancel: () => {
        p.cancel(`${symbols.error} Deploy operation cancelled.`);
        process.exit(0);
      },
    },
  );

  return tfvarsConfigCore;
};

export const deployCommand = async (rootDir: string): Promise<void> => {
  p.intro(`${color.bgBlue(color.white(" Kubrick Deployment "))}`);

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
    await initializeTerraform(terraformDir);

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

    const tfvarsExists = tfvarsFileExists(terraformDir);
    const useExistingTfVars =
      !!tfvarsExists &&
      handleCancel(
        await p.confirm({
          message: `Existing ${color.blue("terraform.tfvars")} file found. Use existing variables?`,
          initialValue: true,
        }),
      );

    // build tfvarsConfig
    const tfvarsConfig: TFVarsConfigCore = useExistingTfVars
      ? (parseTerraformVars(terraformDir) as TFVarsConfig)
      : await promptTfVars();

    await validateAWSCredentials(
      tfvarsConfig.aws_profile,
      tfvarsConfig.aws_region,
    );
    await checkAWSPermissions(
      tfvarsConfig.aws_profile,
      tfvarsConfig.aws_region,
    );

    if (!useExistingTfVars) {
      const { secretName, shouldImport } = await determineSecretName();

      tfvarsConfig.secrets_manager_name = secretName;

      writeTerraformVars(terraformDir, tfvarsConfig as TFVarsConfig);
      p.log.success(`Created ${color.yellow("terraform/terraform.tfvars")}`);

      // Import secret to tfstate if needed (this operation requires terraform.tfvars to exist)
      if (shouldImport) {
        await importSecret(
          terraformDir,
          (tfvarsConfig as TFVarsConfig).secrets_manager_name,
        );
      }
    }

    const confirmDeployStep = handleCancel(
      await p.confirm({
        message: "Start deployment?",
        initialValue: true,
      }),
    );

    if (!confirmDeployStep) {
      p.cancel(`Deployment cancelled by user.`);
      process.exit(1);
    }

    const stdout = await deployTerraform(
      terraformDir,
      tfvarsConfig.aws_profile,
      tfvarsConfig.aws_region,
    );

    p.log.success(
      `${symbols.success} ${color.green("Kubrick deployment completed successfully!")}`,
    );

    const showOutput = handleCancel(
      await p.confirm({
        message: "Print outputs?",
      }),
    );

    if (showOutput) {
      const output = extractOutputs(stdout);
      if (output) {
        p.log.message(output, { symbol: color.cyan("~") });
      } else {
        p.log.error("Could not extract outputs");
      }
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
