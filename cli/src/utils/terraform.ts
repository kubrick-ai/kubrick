import * as p from "@clack/prompts";
import color from "picocolors";
import { existsSync } from "fs";
import { resolve } from "path";
import { runCommand } from "./shell.js";
import type { SecretConfig } from "../types/index.js";
import { symbols } from "./symbols.js";
import { handleCancel } from "./misc.js";

export const checkTerraformVars = async (rootDir: string): Promise<void> => {
  const tfvarsFile = resolve(rootDir, "terraform", "terraform.tfvars");

  // TODO: Handle creating tfvars
  if (!existsSync(tfvarsFile)) {
    p.log.info(
      `terraform.tfvars not found.
Terraform will prompt for required variables during deployment.
Values entered will NOT be saved for future deployments.
To avoid this, create a ${color.yellow("terraform/terraform.tfvars")} file.`,
    );

    const proceed = await p.confirm({
      message: "Continue without terraform.tfvars?",
      initialValue: false,
    });

    if (!proceed) {
      p.cancel("Please create terraform.tfvars and run again");
      process.exit(1);
    }
  } else {
    p.log.success("Found terraform.tfvars");
  }
};

export const getSecretConfig = async (): Promise<SecretConfig> => {
  const secretAction = handleCancel(
    await p.select({
      message: "AWS Secrets Manager configuration",
      options: [
        { value: "create", label: "Create new secret" },
        { value: "import", label: "Import existing secret" },
        { value: "skip", label: "Skip for now" },
      ],
    }),
  ) as "create" | "import" | "skip";

  if (secretAction === "import") {
    const secretName = handleCancel(
      await p.text({
        message: "Enter existing secret name",
        placeholder: "kubrick_secret",
        defaultValue: "kubrick_secret",
        validate: (value) => {
          if (!value) return "Secret name is required";
        },
      }),
    );

    return { action: "import", name: secretName };
  }

  return { action: secretAction };
};

export const initializeTerraform = async (
  terraformDir: string,
): Promise<void> => {
  const terraformStateDir = resolve(terraformDir, ".terraform");

  if (!existsSync(terraformStateDir)) {
    const s = p.spinner();
    s.start(`${symbols.process} Initializing Terraform...`);

    const result = await runCommand("terraform", ["init"], {
      cwd: terraformDir,
    });

    if (!result.success) {
      s.stop(`${symbols.error} Terraform initialization failed`);
      p.cancel(`Terraform init failed: ${result.stderr}`);
      process.exit(1);
    }

    s.stop(`${symbols.success} Initialized Terraform`);
  }
};

export const importSecret = async (
  terraformDir: string,
  secretName: string,
): Promise<void> => {
  const s = p.spinner();
  s.start(`${symbols.key} Importing secret: ${secretName}`);

  const result = await runCommand(
    "terraform",
    [
      "import",
      "module.secrets_manager.aws_secretsmanager_secret.kubrick_secret",
      secretName,
    ],
    { cwd: terraformDir },
  );

  if (!result.success) {
    s.stop(`${symbols.error} Secret import failed`);
    p.note(
      `Failed to import secret: ${result.stderr}\nThis may be normal if the secret is already imported.`,
      `${symbols.warning} Import Warning`,
    );
  } else {
    s.stop(`${symbols.success} Secret imported successfully`);
  }
};

export const deployTerraform = async (
  terraformDir: string,
  secretConfig: SecretConfig,
  profile: string,
  region: string,
): Promise<string> => {
  const s = p.spinner();

  const env: Record<string, string> = {
    AWS_PROFILE: profile,
    AWS_DEFAULT_REGION: region,
  };

  if (secretConfig.action === "import" && secretConfig.name) {
    await importSecret(terraformDir, secretConfig.name);
  }

  s.start(`${symbols.process} Deploying Terraform configuration...`);

  const result = await runCommand("terraform", ["apply"], {
    cwd: terraformDir,
    env,
  });

  if (!result.success) {
    s.stop(`${symbols.error} Terraform deployment failed`);
    p.cancel(`Terraform apply failed: ${result.stderr}`);
    process.exit(1);
  }

  s.stop(`${symbols.success} Infrastructure deployed successfully`);
  return result.stdout;
};
