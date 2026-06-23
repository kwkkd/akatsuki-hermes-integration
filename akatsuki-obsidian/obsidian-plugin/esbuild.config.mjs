import esbuild from "esbuild";
import process from "process";
import builtins from "builtin-modules";

const prod = process.argv[2] === "production";

esbuild
  .build({
    entryPoints: ["src/main.ts"],
    bundle: true,
    external: [
      "obsidian",
      "electron",
      ...builtins,
    ],
    format: "cjs",
    target: "es2018",
    outfile: "dist/main.js",
    sourcemap: prod ? false : "inline",
    treeShaking: true,
    minify: prod,
  })
  .then(() => {
    console.log(`Build ${prod ? "production" : "dev"} → dist/main.js`);
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
