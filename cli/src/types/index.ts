export interface DeploymentConfig {
  aws_profile?: string;
  aws_region?: string;
}

export interface TerraformVarsConfig {
  twelvelabs_api_key: string;
  aws_profile: string;
  aws_region: string;
  secrets_manager_name: string;
  db_username: string;
  db_password: string;
}

export interface AWSCredentials {
  accountId: string;
  userArn: string;
  region?: string;
}

export interface ValidationResult {
  success: boolean;
  failedChecks: string[];
}
