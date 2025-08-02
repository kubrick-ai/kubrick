export interface OperationConfig {
  profile: string;
  region: string;
  skipAuthCheck: boolean;
}

export interface AWSCredentials {
  accountId: string;
  userArn: string;
  region?: string;
}

export interface SecretConfig {
  action: "create" | "import" | "skip";
  name?: string;
}

export interface ValidationResult {
  success: boolean;
  failedChecks: string[];
}
