import { isCancel, cancel } from "@clack/prompts";

export const handleCancel = <T>(result: T): Exclude<T, symbol> => {
  if (isCancel(result)) {
    cancel("Operation cancelled by user.");
    process.exit(0);
  }
  if (typeof result === "symbol") {
    throw new Error("Unexpected symbol value");
  }
  return result as Exclude<T, symbol>;
};

export const extractOutputs = (stdout: string) => {
  return stdout
    .split(/Outputs:\s*\n/)
    .at(-1)
    ?.trimEnd();
};
