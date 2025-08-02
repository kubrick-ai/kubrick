import * as p from "@clack/prompts";
import color from "picocolors";
import { existsSync } from "fs";
import { resolve } from "path";
import { runCommand } from "./shell.js";
import type { SecretConfig } from "../types/index.js";
import { symbols } from "../theme/index.js";
import { handleCancel } from "./misc.js";

export const checkTerraformVars = async (rootDir: string): Promise<void> => {
  const tfvarsFile = resolve(rootDir, "terraform", "terraform.tfvars");

  // TODO: Handle creating tfvars file
  if (!existsSync(tfvarsFile)) {
    p.log.info(
      `terraform.tfvars not found. Create a ${color.yellow("terraform/terraform.tfvars")} file.`,
    );

    p.cancel("Please create terraform.tfvars and run again");
    process.exit(1);
  } else {
    p.log.success("Found terraform.tfvars");
  }
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

export const removeSecret = async (terraformDir: string): Promise<void> => {
  const s = p.spinner();
  s.start(`${symbols.key} Removing secret from deployment configuration`);

  const result = await runCommand(
    "terraform",
    [
      "state",
      "rm",
      "module.secrets_manager.aws_secretsmanager_secret.kubrick_secret",
    ],
    { cwd: terraformDir },
  );

  if (!result.success) {
    s.stop(`${symbols.error} Terraform state mutation failed`);
    p.note(
      `Failed to remove secret: ${result.stderr}\nThis may be normal if the secret resource was never created.`,
      `${symbols.warning} Warning`,
    );
  } else {
    s.stop(
      `${symbols.success} Secret removed from deployment configuration successfully`,
    );
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

  s.start(
    `${symbols.process} Deploying infrastructure. (Grab a coffee, this may take a while)...`,
  );

  const flags = ["-auto-approve", "-input-false"];
  const result = await runCommand("terraform", ["apply", ...flags], {
    cwd: terraformDir,
    env,
  });

  if (!result.success) {
    s.stop(`${symbols.error} Infrastructure deployment failed`);
    p.cancel(`Failed to deploy infrastructure: ${result.stderr}`);
    process.exit(1);
  }

  s.stop(`${symbols.success} Infrastructure deployed successfully`);
  return result.stdout;
};

export const destroyTerraform = async (
  terraformDir: string,
  profile: string,
  region: string,
): Promise<string> => {
  const s = p.spinner();

  const env: Record<string, string> = {
    AWS_PROFILE: profile,
    AWS_DEFAULT_REGION: region,
  };

  const excludeSecret = handleCancel(
    await p.confirm({
      message:
        "Exclude AWS secret from destroy? \
    \nThis is useful if you are planning to redeploy with the same secret.\
     You will have to choose the import existing secret option on your next deploy.",
      initialValue: true,
    }),
  );

  if (excludeSecret) {
    await removeSecret(terraformDir);
  }

  s.start(
    `${symbols.process} Destroying existing infrastructure. (Grab a coffee, this may take a while)...`,
  );

  const flags = ["-destroy", "-auto-approve", "-input-false"];
  const result = await runCommand("terraform", ["apply", ...flags], {
    cwd: terraformDir,
    env,
  });

  if (!result.success) {
    s.stop(`${symbols.error} Destroy operation failed`);
    p.cancel(`Failed to destroy existing infrastructure: ${result.stderr}`);
    process.exit(1);
  }

  s.stop(`${symbols.success} Infrastructure destroyed successfully`);
  return result.stdout;
};
