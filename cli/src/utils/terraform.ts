import * as p from "@clack/prompts";
import color from "picocolors";
import { existsSync, writeFileSync } from "fs";
import { resolve } from "path";
import { runCommand } from "./shell.js";
import { symbols } from "../theme/index.js";
import { handleCancel } from "./misc.js";
import type { TerraformVarsConfig } from "../types/index.js";

export const tfvarsFileExists = (terraformDir: string): boolean => {
  const tfvarsFile = resolve(terraformDir, "terraform.tfvars");
  return existsSync(tfvarsFile);
};

export const writeTerraformVars = (
  terraformDir: string,
  config: TerraformVarsConfig,
): void => {
  const tfvarsFile = resolve(terraformDir, "terraform.tfvars");

  const content = `# Kubrick Terraform Variables
# Generated automatically

# Required:
# TwelveLabs API Key
twelvelabs_api_key = "${config.twelvelabs_api_key}"

# AWS Configuration
aws_profile = "${config.aws_profile}"
aws_region = "${config.aws_region}"

# Secrets Manager
secrets_manager_name = "${config.secrets_manager_name}"

# Database credentials - These will be stored securely in AWS Secrets Manager
db_username = "${config.db_username}"
db_password = "${config.db_password}"
`;

  writeFileSync(tfvarsFile, content, "utf8");
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
      p.cancel(`Terraform init failed: \n${result.stderr}`);
      process.exit(1);
    }

    s.stop(`${symbols.success} Initialized Terraform`);
  }
};

export const getTerraformStateList = async (terraformDir: string) => {
  const result = await runCommand("terraform", ["state", "list"], {
    cwd: terraformDir,
  });
  const stateList = result.stdout.split("\n");
  return stateList;
};

export const secretExistsInTfState = async (terraformDir: string) => {
  const stateList = await getTerraformStateList(terraformDir);
  return stateList.includes(
    "module.secrets_manager.aws_secretsmanager_secret.kubrick_secret",
  );
};

export const initSecret = async (terraformDir: string): Promise<string> => {
  const secretAction = handleCancel(
    await p.select({
      message: "AWS Secrets Manager configuration",
      options: [
        { value: "create", label: "Create new secret" },
        { value: "import", label: "Import existing secret" },
      ],
    }),
  ) as "create" | "import";

  const secretName = handleCancel(
    await p.text({
      message: `Enter ${secretAction === "import" ? "existing" : "new"} secret name`,
      placeholder: "kubrick_secret",
      defaultValue: "kubrick_secret",
      validate: (value) => {
        if (!value) return "Secret name is required";
      },
    }),
  );

  if (secretAction === "import") {
    await importSecret(terraformDir, secretName);
  }

  return secretName;
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
      `Failed to import secret: \n${result.stderr}\nThis may be normal if the secret is already imported.`,
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
      `Failed to remove secret: \n${result.stderr}\nThis may be normal if the secret resource was never created.`,
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
  profile?: string,
  region?: string,
): Promise<string> => {
  const s = p.spinner();

  const env: Record<string, string> = {};
  if (profile) {
    env.AWS_PROFILE = profile;
  }
  if (region) {
    env.AWS_DEFAULT_REGION = region;
  }

  const deployMessage = `${symbols.process} Deploying infrastructure. (Grab a coffee, this may take a while)...`;
  s.start(deployMessage);

  // TODO: Implement progress bar
  const planResult = await runCommand("terraform", ["plan", "-out=tfplan"], {
    cwd: terraformDir,
    env,
  });

  const planOutput = planResult.stdout;
  const match =
    planOutput.match(/Plan: (\d+) to add, (\d+) to change, (\d+) to destroy/) ??
    [];

  const totalResources =
    match[1] && match[2]
      ? parseInt(match[1], 10) + parseInt(match[2], 10)
      : "unknown";

  let isUpdating = false;
  const id = setInterval(async () => {
    if (isUpdating) return; // Skip if previous update still running
    isUpdating = true;

    try {
      const state = await getTerraformStateList(terraformDir);
      s.message(
        `${deployMessage} | Completed: ${state.length}/${totalResources}`,
      );
    } catch (error) {
      // Handle error silently or log
    } finally {
      isUpdating = false;
    }
  }, 10000);

  const flags = ["-auto-approve", "-input=false"];
  const result = await runCommand("terraform", ["apply", ...flags], {
    cwd: terraformDir,
    env,
  });

  clearInterval(id);

  if (!result.success) {
    s.stop(`${symbols.error} Infrastructure deployment failed`);
    p.cancel(`Failed to deploy infrastructure: \n${result.stderr}`);
    process.exit(1);
  }

  s.stop(`${symbols.success} Infrastructure deployed successfully`);
  return result.stdout;
};

export const destroyTerraform = async (
  terraformDir: string,
  profile?: string,
  region?: string,
): Promise<string> => {
  const s = p.spinner();

  const env: Record<string, string> = {};
  if (profile) {
    env.AWS_PROFILE = profile;
  }
  if (region) {
    env.AWS_DEFAULT_REGION = region;
  }

  s.start(`${symbols.process} Checking for existing AWS secret`);
  const secretExists = await secretExistsInTfState(terraformDir);
  s.stop(`${secretExists ? "Existing" : "No existing"} AWS secret found. `);

  if (secretExists) {
    const excludeSecret = handleCancel(
      await p.confirm({
        message: `Exclude existing AWS secret from the destroy operation?
    This is useful if you are planning to redeploy with the same secret.
    You will have to choose the import existing secret option on your next deploy.`,
        initialValue: true,
      }),
    );

    if (excludeSecret) {
      await removeSecret(terraformDir);
    }
  }

  const destroyMessage = `${symbols.process} Destroying existing infrastructure. (Grab a coffee, this may take a while)...`;
  s.start(destroyMessage);

  let isUpdating = false;
  const id = setInterval(async () => {
    if (isUpdating) return; // Skip if previous update still running
    isUpdating = true;

    try {
      const state = await getTerraformStateList(terraformDir);
      s.message(
        `${destroyMessage} | ${state.length} remaining: ${state.join(", ")}`,
      );
    } catch (error) {
      // Handle error silently or log
    } finally {
      isUpdating = false;
    }
  }, 10000);

  const flags = ["-destroy", "-auto-approve", "-input=false"];
  const result = await runCommand("terraform", ["apply", ...flags], {
    cwd: terraformDir,
    env,
  });

  clearInterval(id);

  if (!result.success) {
    s.stop(`${symbols.error} Destroy operation failed`);
    p.cancel(`Failed to destroy existing infrastructure: \n${result.stderr}`);
    process.exit(1);
  }

  s.stop(`${symbols.success} Infrastructure destroyed successfully`);
  return result.stdout;
};
