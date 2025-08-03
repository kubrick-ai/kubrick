import { describe, it, expect } from "vitest";
import { execa } from "execa";
import { resolve } from "path";

describe("CLI e2e tests", () => {
  const cliPath = resolve(process.cwd(), "dist/index.js");

  it("should show help when no arguments provided", async () => {
    const result = await execa("node", [cliPath]);
    expect(result.stdout).toContain("kubrick --help    ");
    expect(result.stdout).toContain("Show this help message");
  }, 10000);

  it("should handle invalid commands gracefully", async () => {
    try {
      const result = await execa("node", [cliPath, "invalid-command"]);
      expect(result.stdout || result.stderr).toBeTruthy();
    } catch (error: any) {
      // Expected to fail with invalid command
      expect(error.stdout || error.stderr).toBeTruthy();
    }
  }, 10000);
});

