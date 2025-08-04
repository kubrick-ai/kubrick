import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  tfvarsFileExists,
  parseTerraformVars,
} from "../../src/utils/terraform.js";
import { readFileSync, existsSync } from "fs";

vi.mock("fs");

describe("terraform utils", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("tfvarsFileExists", () => {
    it("should return true when tfvars file exists", () => {
      vi.mocked(existsSync).mockReturnValue(true);

      const result = tfvarsFileExists("/test/terraform");

      expect(result).toBe(true);
      expect(existsSync).toHaveBeenCalledWith(
        "/test/terraform/terraform.tfvars",
      );
    });

    it("should return false when tfvars file does not exist", () => {
      vi.mocked(existsSync).mockReturnValue(false);

      const result = tfvarsFileExists("/test/terraform");

      expect(result).toBe(false);
    });
  });

  describe("parseTerraformVars", () => {
    it("should throw error when file does not exist", () => {
      vi.mocked(existsSync).mockReturnValue(false);

      expect(() => {
        parseTerraformVars("/test/terraform");
      }).toThrow("terraform.tfvars file not found");
    });

    it("should parse tfvars file correctly", () => {
      const mockContent = `twelvelabs_api_key = "test-api-key"
aws_profile = "test-profile"
aws_region = "us-east-1"
secret_name = "test-secret"
db_username = "testuser"
db_password = "testpass"`;

      vi.mocked(existsSync).mockReturnValue(true);
      vi.mocked(readFileSync).mockReturnValue(mockContent);

      const result = parseTerraformVars("/test/terraform");

      expect(result).toEqual({
        twelvelabs_api_key: "test-api-key",
        aws_profile: "test-profile",
        aws_region: "us-east-1",
        secret_name: "test-secret",
        db_username: "testuser",
        db_password: "testpass",
      });
    });
  });
});

