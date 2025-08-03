import * as p from "@clack/prompts";
import color from "picocolors";
import { runCommand, runCommandSilent } from "./shell.js";
import type { AWSCredentials, ValidationResult } from "../types/index.js";
import { symbols } from "../theme/index.js";
import { handleCancel } from "./misc.js";

export const getAWSProfiles = async (): Promise<Array<string>> => {
  // Get AWS profiles
  const profilesResult = await runCommand("aws", [
    "configure",
    "list-profiles",
  ]);

  if (!profilesResult.success) {
    p.cancel(`${symbols.error} Could not retrieve AWS profiles`);
    process.exit(1);
  }

  const profiles = profilesResult.stdout.split("\n");
  return profiles;
};

export const getAWSRegions = async (): Promise<Array<string>> => {
  // Get AWS regions
  const regionsResult = await runCommand("aws", [
    "ec2",
    "describe-regions",
    "--query",
    "Regions[*].RegionName",
    "--output",
    "json",
  ]);

  if (!regionsResult.success) {
    p.cancel(`${symbols.error} Could not retrieve AWS regions`);
    process.exit(1);
  }

  const regions = JSON.parse(regionsResult.stdout);
  return regions;
};

export const validateAWSCredentials = async (
  profile: string,
  region: string,
): Promise<AWSCredentials> => {
  const s = p.spinner();
  s.start(`${symbols.process} Validating AWS credentials...`);

  const env: Record<string, string> = {
    AWS_PROFILE: profile,
    AWS_DEFAULT_REGION: region,
  };

  // Get AWS identity information
  const identityResult = await runCommand(
    "aws",
    ["sts", "get-caller-identity"],
    { env },
  );
  if (!identityResult.success) {
    s.stop(`${symbols.error} Failed to get AWS identity`);
    p.cancel(
      `Please ensure AWS CLI is authenticated and your profile: ${env.AWS_PROFILE} is configured and valid.`,
    );
    process.exit(1);
  }

  const identity = JSON.parse(identityResult.stdout);
  const credentials: AWSCredentials = {
    accountId: identity.Account,
    userArn: identity.Arn,
    region: region,
  };

  // Validate region
  const regionResult = await runCommandSilent(
    "aws",
    ["ec2", "describe-regions", "--region", region],
    { env },
  );
  if (!regionResult) {
    s.stop(`${symbols.error} AWS region validation failed`);
    p.cancel(`Cannot access AWS region: ${region}`);
    process.exit(1);
  }

  s.stop(`${symbols.success} AWS credentials validated`);

  // Display AWS configuration
  p.note(
    `Account ID: ${color.cyan(credentials.accountId)}\nIdentity: ${color.cyan(credentials.userArn)}${`\nRegion: ${color.cyan(region)}`}`,
    "AWS Configuration",
  );

  return credentials;
};

export const checkAWSPermissions = async (
  profile: string,
  region: string,
): Promise<ValidationResult> => {
  const s = p.spinner();
  s.start(`${symbols.process} Checking AWS permissions...`);

  const env: Record<string, string> = {
    AWS_PROFILE: profile,
    AWS_DEFAULT_REGION: region,
  };

  const failedChecks: string[] = [];

  // Test S3 access
  const s3Result = await runCommandSilent("aws", ["s3", "ls"], { env });
  if (!s3Result) {
    failedChecks.push("S3");
  }

  // Test Lambda access
  const lambdaResult = await runCommandSilent(
    "aws",
    ["lambda", "list-functions", "--max-items", "1"],
    { env },
  );
  if (!lambdaResult) {
    failedChecks.push("Lambda");
  }

  // Test IAM access
  const iamResult = await runCommandSilent(
    "aws",
    ["iam", "list-roles", "--max-items", "1"],
    { env },
  );
  if (!iamResult) {
    failedChecks.push("IAM");
  }

  // Test API Gateway access
  const apiGatewayResult = await runCommandSilent(
    "aws",
    ["apigateway", "get-rest-apis", "--limit", "1"],
    { env },
  );
  if (!apiGatewayResult) {
    failedChecks.push("API Gateway");
  }

  s.stop(`${symbols.success} Checked AWS account permissions`);

  if (failedChecks.length > 0) {
    p.log.warn(
      `Missing permissions: ${color.yellow(failedChecks.join(", "))}\nThe deployment may fail. Consider reviewing your AWS permissions.`,
    );

    const continueAnyway = handleCancel(
      await p.confirm({
        message: "Continue deployment anyway?",
        initialValue: false,
      }),
    );

    if (!continueAnyway) {
      p.cancel(
        `${symbols.error} Operation cancelled due to insufficient permissions`,
      );
      process.exit(1);
    }
  } else {
    p.log.success(`${symbols.success} AWS permissions validated`);
  }

  return {
    success: failedChecks.length === 0,
    failedChecks,
  };
};
