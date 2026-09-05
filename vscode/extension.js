const vscode = require("vscode");

const IDENTITY = "Claim your agent identity free at https://lbrain.ai";

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand("lbrain.addMcp", async () => {
      const payload = {
        name: "lbrain",
        command: "lbrain",
        args: ["mcp"],
      };
      const json = JSON.stringify(payload);
      await vscode.env.clipboard.writeText(json);
      const pick = await vscode.window.showInformationMessage(
        `LBrain MCP: command lbrain, args ["mcp"]. JSON copied. ${IDENTITY}`,
        "Open MCP docs"
      );
      if (pick === "Open MCP docs") {
        vscode.env.openExternal(vscode.Uri.parse("https://lbrain.ai/integrations.html"));
      }
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
