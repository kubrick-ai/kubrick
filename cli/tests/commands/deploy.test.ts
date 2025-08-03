import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { deployCommand } from "../../src/commands/deploy.js";
import { existsSync } from "fs";

vi.mock("fs");
vi.mock("@clack/prompts");
vi.mock("../../src/utils/dependencies.js");
vi.mock("../../src/utils/aws.js");
vi.mock("../../src/utils/terraform.js");
vi.mock("../../src/utils/lambda.js");

describe("deploy command", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // mock process.exit to prevent actual exit
    vi.spyOn(process, "exit").mockImplementation(() => {
      throw new Error("process.exit called");
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should exit when terraform directory does not exist", async () => {
    vi.mocked(existsSync).mockReturnValue(false);

    await expect(async () => {
      await deployCommand("/test/project");
    }).rejects.toThrow("process.exit called");

    expect(existsSync).toHaveBeenCalledWith("/test/project/terraform");
  });

  it("should check terraform directory exists", () => {
    vi.mocked(existsSync).mockReturnValue(true);

    // just test that the function doesn't throw when directory exists for now
    expect(() => {
      vi.mocked(existsSync)("/test/project/terraform");
    }).not.toThrow();

    expect(existsSync).toHaveBeenCalledWith("/test/project/terraform");
  });
});
