# Multiple Repositories Guide

## TL;DR - Just `cd` and Index

**💡 Pro Tip:** Set up shell commands for even faster indexing - see [Shell Setup Guide](SHELL-SETUP.md)

```bash
# Method 1: cd to each repo and index (EASIEST!)
cd ~/project-a
make -C /path/to/Context-Engine index-here COLLECTION=all-repos

cd ~/project-b
make -C /path/to/Context-Engine index-here COLLECTION=all-repos

cd ~/project-c
make -C /path/to/Context-Engine index-here COLLECTION=all-repos

# After shell setup, it's even simpler:
cd ~/project-a && index-here
cd ~/project-b && index-here
cd ~/project-c && index-here

# Method 2: Index from anywhere with full paths
make index-path REPO_PATH=~/project-a REPO_NAME=project-a COLLECTION=all-repos
make index-path REPO_PATH=~/project-b REPO_NAME=project-b COLLECTION=all-repos
make index-path REPO_PATH=~/project-c REPO_NAME=project-c COLLECTION=all-repos

# Done! Your MCP can now search across all 3 repos
```

---

## Quick Answer

**Yes!** You can index multiple repositories into the **same collection** and search across all of them. Each repo is tagged with its name, so you can filter results by repository.

## Option 1: One Collection, Multiple Repos (Recommended)

This is the simplest approach - index all your repos into one collection and filter by repo name when searching.

### Step 1: Index Your First Repository

**Super Easy Way** (just cd to your repo):
```bash
cd ~/my-first-repo
make -C /Users/Shared/OpenSource/Context-Engine index-here COLLECTION=all-repos
```

**Or specify the full path:**
```bash
make index-path REPO_PATH=~/my-first-repo REPO_NAME=myapp COLLECTION=all-repos
```

> **Tip:** Replace `/Users/Shared/OpenSource/Context-Engine` with wherever you cloned this repo

### Step 2: Index Your Second Repository (Same Collection)

```bash
# Just cd and index!
cd ~/my-second-repo
make -C /Users/Shared/OpenSource/Context-Engine index-here COLLECTION=all-repos

# Or with full paths
make index-path REPO_PATH=~/my-second-repo REPO_NAME=backend COLLECTION=all-repos
```

### Step 3: Add as Many as You Want

```bash
cd ~/my-third-repo
make -C /Users/Shared/OpenSource/Context-Engine index-here COLLECTION=all-repos
```

### Step 4: Use from MCP Client

```bash
# Search everything
docker compose run --rm --entrypoint python indexer /work/scripts/hybrid_search.py \
  --query "authentication function" --limit 10

# Search only in a specific repo
docker compose run --rm --entrypoint python indexer /work/scripts/hybrid_search.py \
  --query "authentication function" --repo myapp --limit 10
```

### Step 4: Use from MCP Client

Your MCP client can now search across all repos:

```json
{
  "tool": "repo_search",
  "arguments": {
    "query": "database connection",
    "limit": 10
  }
}
```

Or filter by specific repo (add `repo` filter support - see below).

---

## Option 2: Separate Collections (Isolated Repos)

If you want complete isolation between repos, use different collections.

### Index Each Repo in Its Own Collection

```bash
# Repo 1 -> collection: repo1
make index-path REPO_PATH=/path/to/repo1 REPO_NAME=myapp COLLECTION=repo1

# Repo 2 -> collection: repo2
make index-path REPO_PATH=/path/to/repo2 REPO_NAME=backend COLLECTION=repo2

# Repo 3 -> collection: repo3
make index-path REPO_PATH=/path/to/repo3 REPO_NAME=frontend COLLECTION=repo3
```

### Search a Specific Collection

Set the `COLLECTION_NAME` environment variable when starting the MCP servers:

```bash
# Search repo1
COLLECTION_NAME=repo1 docker compose up -d mcp mcp_indexer

# Or switch collections dynamically in MCP calls
# (pass collection parameter to repo_search)
```

---

## Quick Commands Reference

### Index Multiple Repos (One Collection)

```bash
# Index 3 repos into "all-repos" collection
make index-path REPO_PATH=/Users/me/project-a REPO_NAME=project-a COLLECTION=all-repos
make index-path REPO_PATH=/Users/me/project-b REPO_NAME=project-b COLLECTION=all-repos
make index-path REPO_PATH=/Users/me/project-c REPO_NAME=project-c COLLECTION=all-repos
```

### Search with Repo Filter

```bash
# Search all repos in the collection
docker compose run --rm --entrypoint python indexer \
  /work/scripts/hybrid_search.py \
  --query "user authentication" \
  --limit 10

# Search only project-a
docker compose run --rm --entrypoint python indexer \
  /work/scripts/hybrid_search.py \
  --query "user authentication" \
  --repo project-a \
  --limit 10
```

### List What's in Your Collection

```bash
# Use qdrant_status tool from MCP
# Or query Qdrant directly
curl http://localhost:6333/collections/all-repos
```

---

## How It Works

Each indexed code chunk gets tagged with metadata:

```json
{
  "path": "/work/src/auth.py",
  "repo": "myapp",
  "language": "python",
  "symbol": "authenticate",
  ...
}
```

When you search, you can filter by:
- `repo` - Repository name
- `language` - Programming language  
- `path_glob` - File path patterns
- `kind` - Symbol type (function, class, etc.)

---

## Practical Examples

### Example 1: Microservices (3 repos, 1 collection)

```bash
# Index all your microservices
make index-path REPO_PATH=~/code/auth-service REPO_NAME=auth COLLECTION=microservices
make index-path REPO_PATH=~/code/api-gateway REPO_NAME=gateway COLLECTION=microservices
make index-path REPO_PATH=~/code/user-service REPO_NAME=users COLLECTION=microservices

# Search across all services
# (MCP client will search "microservices" collection)
```

### Example 2: Frontend + Backend (2 collections)

```bash
# Keep frontend and backend separate
make index-path REPO_PATH=~/code/web-app COLLECTION=frontend
make index-path REPO_PATH=~/code/api-server COLLECTION=backend

# Point MCP to frontend when working on UI
COLLECTION_NAME=frontend docker compose restart mcp_indexer

# Switch to backend when working on API
COLLECTION_NAME=backend docker compose restart mcp_indexer
```

### Example 3: Dependencies + Your Code

```bash
# Index your main project
make index-path REPO_PATH=~/myapp REPO_NAME=myapp COLLECTION=dev

# Also index a library you're using heavily
make index-path REPO_PATH=~/vendor/some-lib REPO_NAME=some-lib COLLECTION=dev

# Now search across both
```

---

## Performance Tips

### For Many Small Repos (< 10 repos)
✅ **Use one collection** - Fast, simple, easy to search across all code

### For Many Large Repos (> 10 repos or > 100k files)
✅ **Use separate collections** - Better performance, isolated indexes

### For Monorepos
✅ **Use one collection** - The repo is already unified
✅ **Filter by path** - Use `path_glob` to search specific areas

---

## Updating Repositories

### Re-index a Specific Repo

```bash
# Update just one repo in the collection (incremental)
make index-path REPO_PATH=/path/to/repo1 REPO_NAME=myapp COLLECTION=all-repos

# Force full re-index (drops old points for this repo)
make index-path REPO_PATH=/path/to/repo1 REPO_NAME=myapp COLLECTION=all-repos RECREATE=1
```

### Watch Mode for Multiple Repos

You can't watch multiple repos with one watcher, but you can run multiple watchers:

```bash
# Terminal 1: Watch repo1
HOST_INDEX_PATH=/path/to/repo1 COLLECTION_NAME=all-repos docker compose run --rm watcher

# Terminal 2: Watch repo2  
HOST_INDEX_PATH=/path/to/repo2 COLLECTION_NAME=all-repos docker compose run --rm watcher
```

Or use separate collections and separate watcher services in docker-compose.

---

## Troubleshooting

**Q: How do I know which repos are in my collection?**

```bash
# Search and look at the "repo" field in results
# Or query Qdrant directly:
curl http://localhost:6333/collections/all-repos/points/scroll \
  -d '{"limit":10,"with_payload":true}'
```

**Q: Can I remove just one repo from a collection?**

Yes! Use the prune script with a repo filter:

```bash
# This will remove all points with metadata.repo = "myapp"
# (You'd need to add --repo-filter flag or manually filter in prune.py)
```

Or just drop the entire collection and re-index:

```bash
make index-path REPO_PATH=/path/to/repo1 REPO_NAME=repo1 COLLECTION=all-repos RECREATE=1
make index-path REPO_PATH=/path/to/repo2 REPO_NAME=repo2 COLLECTION=all-repos
```

**Q: Do I need to restart MCP servers after indexing?**

No! The MCP servers read from Qdrant dynamically. Just re-index and the new data is immediately searchable.

---

## Summary

**Simplest Workflow:**
1. Pick one collection name (e.g., "all-repos")
2. Index all your repos into it with different `REPO_NAME` values
3. Search normally - results include all repos
4. Filter by repo name when you want specific results

That's it! 🎉

