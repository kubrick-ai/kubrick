import { isCancel, cancel } from "@clack/prompts";

export const handleCancel = <T>(result: T): Exclude<T, symbol> => {
  if (isCancel(result)) {
    cancel("Deployment cancelled.");
    process.exit(0);
  }
  if (typeof result === "symbol") {
    throw new Error("Unexpected symbol value");
  }
  return result as Exclude<T, symbol>;
};
