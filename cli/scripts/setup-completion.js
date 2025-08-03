#!/usr/bin/env node

import fs from "fs";
import path from "path";
import os from "os";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const setupCompletion = () => {
  try {
    const shell = process.env.SHELL?.split("/").pop();
    const homeDir = os.homedir();
    const completionScript = path.resolve(
      __dirname,
      "../completions/kubrick.bash",
    );

    if (!fs.existsSync(completionScript)) {
      console.log("Completion script not found, skipping setup");
      return;
    }

    const sourceCommand = `source ${completionScript}`;

    if (shell === "bash") {
      const bashrc = path.join(homeDir, ".bashrc");

      if (fs.existsSync(bashrc)) {
        const content = fs.readFileSync(bashrc, "utf8");
        if (!content.includes(sourceCommand)) {
          fs.appendFileSync(
            bashrc,
            `\n# Kubrick CLI completion\n${sourceCommand}\n`,
          );
          console.log("✓ Added kubrick completion to ~/.bashrc");
        }
      }
    } else if (shell === "zsh") {
      const zshrc = path.join(homeDir, ".zshrc");

      if (fs.existsSync(zshrc)) {
        const content = fs.readFileSync(zshrc, "utf8");
        if (!content.includes(sourceCommand)) {
          const bashcompInit = "autoload -U bashcompinit && bashcompinit";
          const additions = `\n# Kubrick CLI completion\n${bashcompInit}\n${sourceCommand}\n`;
          fs.appendFileSync(zshrc, additions);
          console.log("✓ Added kubrick completion to ~/.zshrc");
        }
      }
    }
  } catch (error) {
    // Silently fail - don't break the build process
    console.log("Shell completion setup skipped");
  }
};

setupCompletion();

