# Adding Context-Engine to Claude Desktop

## Prerequisites

1. **Claude Desktop** installed with MCP support
2. **Context-Engine running** - Make sure your services are up:
   ```bash
   docker compose ps
   # Should show: qdrant, mcp, mcp_indexer running
   ```

3. **Your repositories indexed** - Index at least one repo first:
   ```bash
   make index-path REPO_PATH=~/your-project REPO_NAME=myproject
   ```

## Quick Setup (2 Commands)

```bash
# Add the Memory MCP server (for storing/finding memories)
claude mcp add context-memory --scope user -- npx -y mcp-remote http://localhost:8000/sse --transport sse-only

# Add the Indexer MCP server (for code search)
claude mcp add context-indexer --scope user -- npx -y mcp-remote http://localhost:8001/sse --transport sse-only
```

**That's it!** Restart Claude Desktop and you'll have access to all the tools.

## What You Get

Once added, Claude can use these tools:

### From Memory Server (port 8000)
- **store** - Save memories, decisions, conventions
- **find** - Search your saved memories

### From Indexer Server (port 8001)
- **repo_search** - Search your indexed code
- **code_search** - Alias for repo_search
- **context_search** - Search code + memories together
- **context_answer** - Ask questions about your code (with LLM)
- **qdrant_index** - Index new repos
- **qdrant_prune** - Clean up stale entries
- **qdrant_list** - List collections
- **qdrant_status** - Check index status
- **search_tests_for** - Find test files
- **search_config_for** - Find config files
- **search_callers_for** - Find usage/callers
- **search_importers_for** - Find importers
- **change_history_for_path** - Get git history

## Verify It Works

1. **Restart Claude Desktop**

2. **Check the MCP servers are connected:**
   - Look for the MCP icon/indicator in Claude Desktop
   - Should show "context-memory" and "context-indexer" as connected

3. **Test with a simple query:**
   ```
   You: "Search my code for authentication functions"
   
   Claude will use the repo_search tool automatically
   ```

## Troubleshooting

### Error: "Failed to connect"

Make sure Context-Engine is running:
```bash
docker compose ps
# Start if needed:
docker compose up -d mcp mcp_indexer
```

Check endpoints are accessible:
```bash
curl -I http://localhost:8000/sse
curl -I http://localhost:8001/sse
```

### Error: "npx mcp-remote not found"

The `-y` flag should auto-install it, but you can install manually:
```bash
npm install -g mcp-remote
```

### Want to Remove?

```bash
claude mcp remove context-memory --scope user
claude mcp remove context-indexer --scope user
```

### Want to Update?

Just re-run the `claude mcp add` commands - they'll update the configuration.

## Alternative: Manual Configuration

If the `claude mcp add` command doesn't work, you can manually edit Claude's config:

**Location:** `~/.config/claude/claude_desktop_config.json` (Linux/Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

**Add this:**
```json
{
  "mcpServers": {
    "context-memory": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8000/sse", "--transport", "sse-only"]
    },
    "context-indexer": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8001/sse", "--transport", "sse-only"]
    }
  }
}
```

Then restart Claude Desktop.

## Advanced: Using RMCP Endpoints

If Claude Desktop supports HTTP/RMCP directly (check latest docs):

```bash
# RMCP endpoints (may not need mcp-remote bridge)
claude mcp add context-memory-http --scope user --url http://localhost:8002/mcp
claude mcp add context-indexer-http --scope user --url http://localhost:8003/mcp
```

But as of now, the SSE endpoints with `mcp-remote` bridge are more reliable.

## Usage Examples

Once connected, you can ask Claude:

**Code Search:**
- "Search my code for database connection logic"
- "Find all Python functions that handle authentication"
- "Show me where the User model is defined"

**Memory:**
- "Store this: Our API uses port 3000 in development"
- "Remember: Always run migrations before deploying"
- "Find my notes about the deployment process"

**Combined:**
- "Search my code and memories for information about the testing setup"
- "How does our authentication system work?" (uses context_answer)

**Indexing:**
- "Index the repository at ~/my-new-project"
- "Show me the status of the code index"
- "Prune stale entries from the index"

## Next Steps

1. **Index more repositories:** See [docs/MULTI-REPO.md](MULTI-REPO.md)
2. **Add memories:** Use the `store` tool to save team knowledge
3. **Enable decoder:** Add Ollama for Q&A - see [docs/OLLAMA.md](OLLAMA.md)

That's it! You now have powerful code search and memory right inside Claude Desktop. 🚀

