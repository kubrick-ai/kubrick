import { asciiBanner } from "./ascii.js";
import gradient from "gradient-string";

export const banner = gradient([
  { color: "#F8D454", pos: 0 },
  { color: "#FD8050", pos: 0.5 },
  { color: "#61EAD3", pos: 0.75 },
  { color: "#39B7D4", pos: 1 },
]).multiline(asciiBanner);

export const symbols = {
  success: "✓",
  error: "✗",
  warning: "⚠",
  process: "⚒",
  key: "⚿",
} as const;
