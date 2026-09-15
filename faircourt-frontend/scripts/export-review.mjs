import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const results = path.join(root, "test-results");
const status = JSON.parse(
  fs.readFileSync(path.join(results, ".last-run.json"), "utf8"),
);
if (status.status !== "passed")
  throw new Error(
    "Ejecuta primero la batería completa con todas las pruebas correctas.",
  );
const captures = fs
  .readdirSync(results, { withFileTypes: true })
  .filter(
    (entry) => entry.isDirectory() && entry.name.startsWith("frontend-visual-"),
  )
  .flatMap((entry) => {
    const directory = path.join(results, entry.name, "screenshots");
    return fs
      .readdirSync(directory)
      .filter((name) => name.endsWith(".png"))
      .map((name) => ({ name, source: path.join(directory, name) }));
  });
if (captures.length !== 30)
  throw new Error(
    "Se esperaban las 30 capturas de la batería completa; encontradas: " +
      captures.length,
  );
const output = path.resolve(root, "../docs/images/frontend/current");
fs.mkdirSync(output, { recursive: true });
for (const capture of captures)
  fs.copyFileSync(capture.source, path.join(output, capture.name));
console.log(
  "Exportadas 30 capturas verificadas a docs/images/frontend/current.",
);
