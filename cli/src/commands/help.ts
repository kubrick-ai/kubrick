import color from "picocolors";

export const helpCommand = () => {
  console.log(`
${color.cyan(color.bold("Kubrick CLI"))} - Deploy Kubrick infrastructure with Lambda packages and Terraform

${color.yellow("Usage:")}
  ${color.green("kubrick")} ${color.blue("<command>")} ${color.gray("[options]")}

${color.yellow("Commands:")}
  ${color.green("deploy")}        Deploy new or existing Kubrick infrastructure
  ${color.green("destroy")}       Destroy existing Kubrick infrastructure

${color.yellow("Options:")}
  ${color.gray("--help, -h")}    Show this help message

${color.yellow("Examples:")}
  ${color.green("kubrick deploy")}    Deploy with interactive prompts
  ${color.green("kubrick destroy")}   Destroy with interactive prompts
  ${color.green("kubrick --help")}    Show this help message
`);
  process.exit(0);
};
