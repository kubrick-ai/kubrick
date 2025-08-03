export interface TFVarsConfigCore {
  twelvelabs_api_key: string;
  aws_profile: string;
  aws_region: string;
  db_username: string;
  db_password: string;
  secrets_manager_name?: string;
}

export interface TFVarsConfig extends TFVarsConfigCore {
  secrets_manager_name: string;
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
