---
name: mcp-integration
description: Model Context Protocol (MCP) integration patterns for Claude Code. Provides standardized tool discovery, invocation, and lifecycle management for extending AI capabilities through external servers and data sources.
tags: [mcp, protocol, tool-integration, discovery, claude-code]
version: 1.0.0
source: Based on Anthropic MCP specification, Linux Foundation MCP standard
integrated-with: super-skill v3.7+
---

# MCP Integration Skill

This skill provides comprehensive Model Context Protocol (MCP) integration patterns for Claude Code, enabling standardized connections to external tools, data sources, and AI capabilities.

## Core Concepts

### What is MCP?

```
┌─────────────────────────────────────────────────────────────────┐
│               MODEL CONTEXT PROTOCOL (MCP)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   "USB Interface for AI" - Universal standard for tool plugins  │
│                                                                  │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│   │ Claude   │────│ MCP      │────│ External │               │
│   │ Code     │     │ Protocol │     │ Tools    │               │
│   └──────────┘     └──────────┘     └──────────┘               │
│                                                                  │
│   Features:                                                      │
│   • Standardized Integration                                     │
│   • Tool Discovery & Auto-Detection                             │
│   • Unified JSON-RPC 2.0 Invocation                             │
│   • 100+ MCP Server Ecosystem                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Transport Modes

| Mode | How It Works | Best For |
|------|-------------|----------|
| **stdio (local)** | MCP server runs as subprocess | 80% of use cases; local tools |
| **http (remote)** | Connects to remote HTTP servers | Cloud services, OAuth |
| **sse** | Server-Sent Events (deprecated) | Being replaced by HTTP |

## Configuration Scopes

```yaml
scopes:
  local:
    location: ./.mcp.json
    use_case: Project-specific, sensitive credentials

  project:
    location: .mcp.json (shared in repo)
    use_case: Team-wide unified configuration

  user:
    location: ~/.mcp/config.json
    use_case: Cross-project reusable tools
```

## Installation Commands

### Remote HTTP Server
```bash
# Basic syntax
claude mcp add --transport http <name> <url>

# Example: Notion
claude mcp add --transport http notion https://mcp.notion.com/mcp

# With Bearer token
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer your-token"
```

### Local stdio Server
```bash
# Basic syntax
claude mcp add [options] <name> -- <command> [args...]

# Example: GitHub
claude mcp add --scope user github -- npx -y @modelcontextprotocol/server-github

# Example: Filesystem
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem /path/to/allow
```

## Popular MCP Servers

| Server | Purpose | Capabilities |
|--------|---------|--------------|
| **GitHub** | Repository collaboration | Issues, PRs, commits, CI status |
| **Filesystem** | File I/O operations | Read/write files, directory listing |
| **Playwright** | Browser automation | E2E testing, screenshots, DOM extraction |
| **Sentry** | Error monitoring | Query errors, stack traces, trends |
| **Vercel** | Deployment management | Deploy logs, rollbacks, env vars |
| **PostgreSQL** | Database queries | Direct SQL execution |
| **Notion** | Document management | Read/write Notion pages |
| **Context7** | Real-time documentation | Latest API docs, examples |

## Implementation Patterns

### MCP Server Configuration

```python
class MCPServerConfig:
    """
    Configuration for an MCP server connection.
    """

    def __init__(
        self,
        name: str,
        transport: str,  # 'stdio' | 'http'
        command: str | None = None,  # for stdio
        url: str | None = None,  # for http
        env: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        scope: str = "user"  # 'local' | 'project' | 'user'
    ):
        self.name = name
        self.transport = transport
        self.command = command
        self.url = url
        self.env = env or {}
        self.headers = headers or {}
        self.scope = scope

    def to_config(self) -> dict:
        """Generate configuration for .mcp.json"""
        if self.transport == "stdio":
            return {
                "mcpServers": {
                    self.name: {
                        "command": self.command,
                        "args": [],
                        "env": self.env
                    }
                }
            }
        else:  # http
            return {
                "mcpServers": {
                    self.name: {
                        "url": self.url,
                        "headers": self.headers
                    }
                }
            }
```

### Tool Discovery & Invocation

```python
class MCPToolManager:
    """
    Manages MCP tool discovery and invocation.
    """

    async def discover_tools(self, server_name: str) -> list[dict]:
        """
        Discover available tools from an MCP server.
        """
        # MCP uses JSON-RPC 2.0 for communication
        request = {
            "jsonrpc": "2.0",
            "id": generate_id(),
            "method": "tools/list"
        }

        response = await self.send_request(server_name, request)
        return response.get("result", {}).get("tools", [])

    async def invoke_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict
    ) -> dict:
        """
        Invoke a tool on an MCP server.
        """
        request = {
            "jsonrpc": "2.0",
            "id": generate_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        response = await self.send_request(server_name, request)
        return response.get("result", {})

    async def handle_list_changed(self, server_name: str):
        """
        Handle dynamic tool updates from servers.
        MCP servers can notify when tools change.
        """
        # Re-discover tools when notified
        tools = await self.discover_tools(server_name)
        self.update_tool_registry(server_name, tools)
```

### Resource & Prompt Templates

```python
class MCPResourceManager:
    """
    Manages MCP resources and prompt templates.
    """

    async def list_resources(self, server_name: str) -> list[dict]:
        """List available resources from server."""
        request = {
            "jsonrpc": "2.0",
            "id": generate_id(),
            "method": "resources/list"
        }
        response = await self.send_request(server_name, request)
        return response.get("result", {}).get("resources", [])

    async def read_resource(
        self,
        server_name: str,
        uri: str
    ) -> str | bytes:
        """Read a specific resource by URI."""
        request = {
            "jsonrpc": "2.0",
            "id": generate_id(),
            "method": "resources/read",
            "params": {"uri": uri}
        }
        response = await self.send_request(server_name, request)
        return response.get("result", {}).get("contents", [])

    async def get_prompt(
        self,
        server_name: str,
        prompt_name: str,
        arguments: dict | None = None
    ) -> dict:
        """Get a prompt template from server."""
        request = {
            "jsonrpc": "2.0",
            "id": generate_id(),
            "method": "prompts/get",
            "params": {
                "name": prompt_name,
                "arguments": arguments or {}
            }
        }
        response = await self.send_request(server_name, request)
        return response.get("result", {})
```

## Security Best Practices

### 1. Server Trust Verification
```python
async def verify_server_trust(server_config: MCPServerConfig) -> bool:
    """
    Verify MCP server is from a trusted source.
    """
    # Check if from official registry
    if server_config.name in OFFICIAL_MCP_SERVERS:
        return True

    # Use MCP-Scan for security scanning
    scan_result = await mcp_scan(server_config)
    return scan_result.is_safe
```

### 2. Scope Isolation
```python
def get_scope_config(scope: str) -> str:
    """
    Get configuration file path for scope.
    """
    paths = {
        "local": "./.mcp.json",
        "project": ".mcp.json",
        "user": "~/.mcp/config.json"
    }
    return paths.get(scope, paths["user"])

def isolate_credentials(server_name: str, scope: str):
    """
    Ensure sensitive credentials are in local scope only.
    """
    if has_sensitive_data(server_name) and scope != "local":
        raise SecurityError(
            "Sensitive credentials must use 'local' scope"
        )
```

### 3. Input Sanitization
```python
def sanitize_tool_input(tool_name: str, arguments: dict) -> dict:
    """
    Sanitize tool inputs to prevent injection attacks.
    """
    # Check for prompt injection patterns
    for key, value in arguments.items():
        if isinstance(value, str):
            if contains_injection_pattern(value):
                raise SecurityError(
                    f"Potential injection detected in {key}"
                )

    # Validate against tool schema
    schema = get_tool_schema(tool_name)
    validate_arguments(schema, arguments)

    return arguments
```

## Environment Variables

```bash
# Configure timeout (ms)
export MCP_TIMEOUT=10000

# Increase output token limit
export MAX_MCP_OUTPUT_TOKENS=50000

# Enable debug logging
export MCP_DEBUG=true
```

## Management Commands

```bash
# List all configured servers
claude mcp list

# Get server details
claude mcp get github

# Remove a server
claude mcp remove github

# Interactive management
/mcp
```

## Integration with Super-Skill

### Phase Integration

```yaml
phase_mcp_mapping:
  phase_2_github_discovery:
    servers: [github, filesystem]
    tools: [search_repos, clone_repo, read_files]

  phase_8_development:
    servers: [filesystem, postgresql, playwright]
    tools: [read/write_files, query_db, browser_test]

  phase_9_qa:
    servers: [playwright, sentry]
    tools: [e2e_test, error_tracking]

  phase_11_deployment:
    servers: [vercel, github]
    tools: [deploy, create_release]
```

### Dynamic Tool Discovery

```python
async def enhance_phase_with_mcp(phase: int, context: dict):
    """
    Enhance phase execution with MCP-discovered tools.
    """
    # Get required capabilities for phase
    required = PHASE_CAPABILITIES[phase]

    # Discover matching MCP tools
    discovered_tools = []
    for server in get_active_servers():
        tools = await mcp_manager.discover_tools(server)
        for tool in tools:
            if matches_capabilities(tool, required):
                discovered_tools.append({
                    "server": server,
                    "tool": tool,
                    "priority": calculate_priority(tool, context)
                })

    # Sort by priority and return top matches
    discovered_tools.sort(key=lambda x: x["priority"], reverse=True)
    return discovered_tools[:5]
```

## OAuth Authentication

```python
class MCPOAuthHandler:
    """
    Handle OAuth flows for remote MCP servers.
    """

    async def authenticate(
        self,
        server_name: str,
        auth_url: str
    ) -> dict:
        """
        Complete OAuth authentication flow.
        """
        # Open browser for user authorization
        await open_browser(auth_url)

        # Wait for callback with auth code
        auth_code = await wait_for_callback()

        # Exchange code for tokens
        tokens = await exchange_code_for_tokens(auth_code)

        # Store tokens securely
        await store_tokens_securely(server_name, tokens)

        return tokens

    async def refresh_tokens(
        self,
        server_name: str
    ) -> dict:
        """
        Refresh expired OAuth tokens.
        """
        current = await get_stored_tokens(server_name)
        refreshed = await oauth_refresh(current.refresh_token)
        await store_tokens_securely(server_name, refreshed)
        return refreshed
```

## Checklist

### Before Adding MCP Server
- [ ] Server from trusted source (official registry or verified)
- [ ] Security scanned with MCP-Scan
- [ ] Appropriate scope selected
- [ ] Environment variables configured
- [ ] Required permissions understood

### During Usage
- [ ] Input sanitization active
- [ ] Output validation performed
- [ ] Rate limits respected
- [ ] Error handling in place
- [ ] Audit logging enabled

### After Integration
- [ ] Tools discovered and documented
- [ ] Tests written for tool invocations
- [ ] Documentation updated
- [ ] Team notified of new capabilities

## Deliverables

- MCP server configurations
- Tool discovery documentation
- Security audit report
- Integration test suite

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Anthropic MCP Documentation](https://docs.anthropic.com/claude-code/mcp)
- [MCP Server Registry](https://github.com/topics/mcp)
- [MCP Security Guide](https://modelcontextprotocol.io/security)
- [MCP-Scan Security Tool](https://github.com/protectai/MCP-Scan)
