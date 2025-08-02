import { execa } from "execa";

export const commandExists = async (command: string): Promise<boolean> => {
  try {
    await execa("which", [command]);
    return true;
  } catch {
    return false;
  }
};

export const runCommand = async (
  command: string,
  args: string[] = [],
  options: { cwd?: string; env?: Record<string, string> } = {},
): Promise<{ stdout: string; stderr: string; success: boolean }> => {
  try {
    const result = await execa(command, args, {
      cwd: options.cwd,
      env: { ...process.env, ...options.env },
    });
    return {
      stdout: result.stdout,
      stderr: result.stderr,
      success: true,
    };
  } catch (error: any) {
    return {
      stdout: error.stdout || "",
      stderr: error.stderr || error.message,
      success: false,
    };
  }
};

export const runCommandSilent = async (
  command: string,
  args: string[] = [],
  options: { cwd?: string; env?: Record<string, string> } = {},
): Promise<boolean> => {
  try {
    await execa(command, args, {
      cwd: options.cwd,
      env: { ...process.env, ...options.env },
      stdout: "ignore",
      stderr: "ignore",
    });
    return true;
  } catch {
    return false;
  }
};

