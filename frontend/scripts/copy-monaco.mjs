// Copies the Monaco editor distribution into public/ so the app serves the
// editor itself instead of depending on a runtime CDN. Idempotent: skips the
// copy when the target already matches the installed monaco-editor version.
import { cpSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "node_modules", "monaco-editor", "min", "vs");
const dest = join(root, "public", "monaco", "vs");
const stampFile = join(root, "public", "monaco", ".version");

const pkg = JSON.parse(readFileSync(join(root, "node_modules", "monaco-editor", "package.json"), "utf8"));
const version = pkg.version;

let stamped = null;
try {
  stamped = readFileSync(stampFile, "utf8").trim();
} catch {
  // no stamp yet
}

if (stamped === version && existsSync(join(dest, "loader.js"))) {
  console.log(`Monaco ${version} already present in public/monaco — skipping copy.`);
  process.exit(0);
}

mkdirSync(dirname(dest), { recursive: true });
cpSync(src, dest, { recursive: true });
writeFileSync(stampFile, version);
console.log(`Copied Monaco ${version} to public/monaco/vs.`);
