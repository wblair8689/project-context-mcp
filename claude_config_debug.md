## 🔧 Claude Desktop MCP Configuration

**Temporary Diagnostic Configuration:**

Update your Claude Desktop MCP settings to use the debug server:

```json
{
  "mcpServers": {
    "project_context": {
      "command": "python",
      "args": ["/Users/williamblair/AI-Game-Evolution-Platform/project_context_mcp/debug_server.py"],
      "env": {}
    }
  }
}
```

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**After updating:**
1. Save the config file
2. Restart Claude Desktop
3. Check the logs at `/Users/williamblair/Library/Logs/Claude/mcp-server-project_context.log`

**This will give us detailed diagnostic output to see exactly what's failing.**

---

**Alternatively, you can:**

1. Use the original config but restart Claude Desktop completely (quit and reopen)
2. Check if there are any file permission issues
3. Verify the path is correct in your config

**Original config should be:**
```json
{
  "mcpServers": {
    "project_context": {
      "command": "python",
      "args": ["/Users/williamblair/AI-Game-Evolution-Platform/project_context_mcp/context_server.py"],
      "env": {}
    }
  }
}
```
