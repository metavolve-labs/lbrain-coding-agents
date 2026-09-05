#!/usr/bin/env node
const { spawn } = require("child_process");
const path = require("path");
const root = path.resolve(__dirname, "..");
const args = ["-m", "lbrain_agents", ...process.argv.slice(2)];
const child = spawn("python3", args, { stdio: "inherit", cwd: root, env: process.env });
child.on("exit", (code) => process.exit(code == null ? 1 : code));
