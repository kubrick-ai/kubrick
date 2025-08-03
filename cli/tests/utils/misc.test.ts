import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleCancel, extractOutputs } from "../../src/utils/misc.js";
import { isCancel } from "@clack/prompts";

vi.mock("@clack/prompts");

describe("misc utils", () => {
  describe("handleCancel", () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it("should return value when not cancelled", () => {
      vi.mocked(isCancel).mockReturnValue(false);
      const result = handleCancel("test");
      expect(result).toBe("test");
    });

    it("should exit process when cancelled", () => {
      const mockExit = vi.spyOn(process, "exit").mockImplementation(() => {
        throw new Error("process.exit called");
      });

      // Mock isCancel to return true for our test
      vi.mocked(isCancel).mockReturnValue(true);

      expect(() => {
        handleCancel(Symbol.for("clack.cancel"));
      }).toThrow("process.exit called");

      mockExit.mockRestore();
    });

    it("should throw error for unexpected symbol", () => {
      vi.mocked(isCancel).mockReturnValue(false);
      expect(() => {
        handleCancel(Symbol("test"));
      }).toThrow("Unexpected symbol value");
    });
  });

  describe("extractOutputs", () => {
    it("should extract outputs from terraform destroy output", () => {
      const input = `
No changes. No objects need to be destroyed.

Either you have not created any objects yet or the existing objects were already deleted outside of Terraform.

Destroy complete! Resources: 0 destroyed.
`;
      const result = extractOutputs(input);
      expect(result).toBe(`
No changes. No objects need to be destroyed.

Either you have not created any objects yet or the existing objects were already deleted outside of Terraform.

Destroy complete! Resources: 0 destroyed.`);
    });

    it("should extract outputs from terraform plan output", () => {
      const input = `
    }

Plan: 147 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + api_gateway_arn                   = (known after apply)
  + api_gateway_execution_arn         = (known after apply)
  + api_gateway_id                    = (known after apply)
  + api_gateway_invoke_url            = (known after apply)
  + api_gateway_stage_name            = "v1_0"
  + cloudfront_arn                    = (known after apply)
  + cloudfront_distribution_id        = (known after apply)
  + cloudfront_domain_name            = (known after apply)
  + cloudfront_status                 = (known after apply)
  + generate_upload_link_endpoint_url = (known after apply)
  + kubrick_playground_bucket_name    = (known after apply)
  + kubrick_video_upload_bucket_name  = (known after apply)
  + s3_bucket_arn                     = (known after apply)
  + s3_bucket_domain_name             = (known after apply)
  + s3_bucket_id                      = (known after apply)
  + search_endpoint_url               = (known after apply)
  + sqs_queue_arn                     = (known after apply)
  + sqs_queue_name                    = "dev-embedding-task-queue"
  + sqs_queue_url                     = (known after apply)
  + tasks_endpoint_url                = (known after apply)
  + videos_endpoint_url               = (known after apply)


`;
      const result = extractOutputs(input);
      expect(result)
        .toBe(`  + api_gateway_arn                   = (known after apply)
  + api_gateway_execution_arn         = (known after apply)
  + api_gateway_id                    = (known after apply)
  + api_gateway_invoke_url            = (known after apply)
  + api_gateway_stage_name            = "v1_0"
  + cloudfront_arn                    = (known after apply)
  + cloudfront_distribution_id        = (known after apply)
  + cloudfront_domain_name            = (known after apply)
  + cloudfront_status                 = (known after apply)
  + generate_upload_link_endpoint_url = (known after apply)
  + kubrick_playground_bucket_name    = (known after apply)
  + kubrick_video_upload_bucket_name  = (known after apply)
  + s3_bucket_arn                     = (known after apply)
  + s3_bucket_domain_name             = (known after apply)
  + s3_bucket_id                      = (known after apply)
  + search_endpoint_url               = (known after apply)
  + sqs_queue_arn                     = (known after apply)
  + sqs_queue_name                    = "dev-embedding-task-queue"
  + sqs_queue_url                     = (known after apply)
  + tasks_endpoint_url                = (known after apply)
  + videos_endpoint_url               = (known after apply)`);
    });
  });
});

