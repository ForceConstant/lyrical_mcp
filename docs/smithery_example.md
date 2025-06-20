---
title: 'Python Quick Start'
description: 'Build and deploy a Python MCP server using FastMCP'
---

# Python Quick Start

Build a Python MCP server with FastMCP and deploy it on Smithery using the proper package structure.

**FastMCP with proper Smithery deployment:**
```python

def get_mcp():
    """Lazy-loaded FastMCP instance to avoid import-time dependencies."""
    from mcp.server.fastmcp import FastMCP
    return FastMCP("weather-server")

def setup_tools(mcp):
    @mcp.tool()
    async def get_weather(city: str) -> str:
        """Get weather for a city."""
        return f"Weather in {city}: Sunny, 72°F"

def main():
    mcp = get_mcp()
    setup_tools(mcp)
    mcp.run()  # Uses stdio transport for Smithery

if __name__ == "__main__":
    main()
```

## 1. Setup

```bash
mkdir weather-mcp && cd weather-mcp
python -m venv venv && source venv/bin/activate
pip install --upgrade pip
```

**Required Project Structure for Smithery:**
```
weather-mcp/
├── pyproject.toml           # Package configuration with console scripts
├── smithery.yaml           # Smithery deployment configuration  
├── Dockerfile              # Container build instructions
└── weather_mcp/            # Python package directory
    ├── __init__.py
    └── server.py           # Main server code
```

**Create the package structure:**
```bash
mkdir weather_mcp
touch weather_mcp/__init__.py
```

## 2. Create Package Configuration

`pyproject.toml`:
```toml
[project]
name = "weather-mcp"
version = "0.1.0"
description = "MCP server for weather information"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.7.1",
    "httpx>=0.25.0",
    "uvicorn>=0.23.1"
]

[project.scripts]
weather-mcp = "weather_mcp.server:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["weather_mcp"]
```

## 3. Build Your Server

`weather_mcp/server.py`:

```python
from typing import Dict, Any
import os

# Lazy loading to prevent tool scanning timeouts
def get_mcp():
    """Lazy-loaded FastMCP instance to avoid import-time dependencies."""
    from mcp.server.fastmcp import FastMCP
    return FastMCP("weather-server")

def get_http_client():
    """Lazy-loaded HTTP client to avoid import-time dependencies."""
    import httpx
    return httpx.AsyncClient(timeout=10.0)

def get_weather_api_url():
    """Lazy-loaded weather API URL."""
    return "https://wttr.in"

def setup_tools(mcp):
    """Setup tools on the MCP server instance."""
    
    @mcp.tool()
    async def ping() -> str:
        """Simple ping tool to test server responsiveness and prevent timeouts."""
        return "pong"

    @mcp.tool()
    async def health_check() -> Dict[str, Any]:
        """Health check to verify server connectivity and status."""
        from datetime import datetime
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "server": "weather-mcp",
            "version": "1.0.0",
            "tools_available": ["ping", "health_check", "get_weather", "compare_weather"]
        }

    @mcp.tool()
    async def get_weather(city: str, units: str = "metric", detailed: bool = False) -> Dict[str, Any]:
        """Get current weather for a city."""
        if not city:
            return {"error": "City name required"}
        
        try:
            # Lazy load dependencies
            from urllib.parse import quote
            
            async with get_http_client() as client:
                response = await client.get(
                    f"{get_weather_api_url()}/{quote(city)}",
                    params={"format": "j1", "m": "" if units == "metric" else "f"}
                )
                response.raise_for_status()
                
            data = response.json()
            current = data["current_condition"][0]
            
            result = {
                "city": city,
                "temperature": f"{current['temp_C']}°C" if units == "metric" else f"{current['temp_F']}°F",
                "condition": current["weatherDesc"][0]["value"],
                "humidity": f"{current['humidity']}%",
                "wind": f"{current['windspeedKmph']} km/h" if units == "metric" else f"{current['windspeedMiles']} mph"
            }
            
            if detailed:
                result["forecast"] = [
                    {
                        "date": day["date"],
                        "max": f"{day['maxtempC']}°C",
                        "min": f"{day['mintempC']}°C",
                        "condition": day["hourly"][4]["weatherDesc"][0]["value"]
                    }
                    for day in data["weather"][:3]
                ]
                
            return result
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def compare_weather(cities: list[str], metric: str = "temperature") -> Dict[str, Any]:
        """Compare weather between multiple cities."""
        if not cities or len(cities) > 5:
            return {"error": "Provide 1-5 cities"}
        
        comparisons = []
        for city in cities:
            weather = await get_weather(city)
            if "error" not in weather:
                comparisons.append({
                    "city": city,
                    "temperature": weather["temperature"],
                    "humidity": weather["humidity"],
                    "wind": weather["wind"]
                })
        
        # Sort by metric
        if metric in ["temperature", "humidity", "wind"]:
            comparisons.sort(
                key=lambda x: float(x[metric].split()[0].replace("°C", "").replace("%", "")), 
                reverse=True
            )
        
        return {"metric": metric, "cities": comparisons}

def main():
    """Main entry point for the weather MCP server."""
    # Lazy initialization - only create mcp instance when needed
    mcp = get_mcp()
    setup_tools(mcp)
    
    print("🌐 Starting weather MCP server")
    mcp.run()

if __name__ == "__main__":
    main()
```

## 4. Configure for Smithery

`smithery.yaml`:
```yaml
# Smithery configuration file: https://smithery.ai/docs/config#smitheryyaml

startCommand:
  type: stdio
  configSchema:
    type: object
    properties:
      units:
        type: string
        description: "Default units for weather (metric/imperial)"
        default: "metric"
        enum: ["metric", "imperial"]
      timeout:
        type: number
        description: "Request timeout in seconds"
        default: 10
        minimum: 5
        maximum: 30
    default: {}
    description: Weather MCP server configuration
  commandFunction:
    |-
    (config) => ({command: 'weather-mcp'})
  exampleConfig:
    units: "metric"
    timeout: 10
```

`Dockerfile`:
```dockerfile
# Generated by https://smithery.ai. See: https://smithery.ai/docs/config#dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Copy source
COPY . /app

# Install Python dependencies and the MCP server
RUN pip install --no-cache-dir .

# Use the console script entrypoint
CMD ["weather-mcp"]
```

**Key Requirements for Smithery:**
- **Package Structure**: Must use proper Python package with `pyproject.toml`
- **Console Script**: Define entry point in `[project.scripts]` section
- **stdio Transport**: Use `mcp.run()` without transport parameter (defaults to stdio)
- **Lazy Loading**: Use lazy imports to prevent tool scanning timeouts
- **CommandFunction**: JavaScript function that generates CLI command

## 5. Test Locally

**Install and test the package:**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Install in development mode
pip install -e .

# Test the console script
weather-mcp
```

**Claude Desktop/Claude Code:**
```json
{
  "mcpServers": {
    "weather-local": {
      "command": "weather-mcp"
    }
  }
}
```

**MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector weather-mcp
```

## 6. Deploy to Smithery

```bash
git init && git add .
git commit -m "Weather MCP server with proper Smithery structure"
git push -u origin main
```

1. Go to [smithery.ai/new](https://smithery.ai/new)
2. Connect your GitHub repository  
3. Deploy! (Smithery will detect the package structure automatically)

**Expected deployment output:**
```
Building Docker image...
Successfully installed weather-mcp-0.1.0
Deployment successful.
Scanning for tools...
Server tools successfully scanned.
```

## 7. Connect Your Server

```json
{
  "mcpServers": {
    "weather": {
      "command": "npx",
      "args": ["-y", "@smithery/cli", "run", "@username/weather-mcp"]
    }
  }
}
```

## Troubleshooting

### Tool Scanning Timeout (MCP error -32001)
**Root Cause**: Import-time dependencies cause FastMCP to timeout during tool discovery.

**Solution**: Use lazy loading pattern:
```python
# ❌ Incorrect (causes timeouts)
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("server")

# ✅ Correct (lazy loading)
def get_mcp():
    from mcp.server.fastmcp import FastMCP
    return FastMCP("server")

def get_http_client():
    import httpx
    return httpx.AsyncClient()
```

### Package Structure Issues
**Error**: `weather-mcp` command not found after deployment

**Solution**: Verify your `pyproject.toml` has correct console script:
```toml
[project.scripts]
weather-mcp = "weather_mcp.server:main"  # Must match package structure
```

### Function Definition Errors
**Error**: "Internal error while deploying" after successful Docker build

**Solution**: Check for:
- Proper function indentation (tools should be at same level)
- All tools have `@mcp.tool()` decorator
- Functions are not nested inside each other

## Best Practices

### Lazy Loading Pattern
Always use lazy loading to prevent tool scanning timeouts:
```python
def get_mcp():
    """Lazy-loaded FastMCP instance to avoid import-time dependencies."""
    from mcp.server.fastmcp import FastMCP
    return FastMCP("server-name")

def setup_tools(mcp):
    """Setup tools on the MCP server instance."""
    
    @mcp.tool()
    async def my_tool():
        # Lazy load dependencies inside tools
        import some_heavy_library
        return some_heavy_library.process()
```

### Error Handling
Include proper error handling in all tools:
```python
@mcp.tool()
async def api_call(query: str) -> Dict[str, Any]:
    """Make an API call with proper error handling."""
    try:
        async with get_http_client() as client:
            response = await client.get(f"https://api.example.com/{query}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}
```

## Next Steps

**Learn More About MCP:**
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/docs) - Official MCP docs
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) - Deep dive into FastMCP features
- [MCP Specification](https://spec.modelcontextprotocol.io/) - Technical protocol specification
- [MCP Python SDK: FastMCP examples](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/fastmcp)

**Explore Smithery:**
- [Browse popular MCP Servers](https://smithery.ai/search?q=is%3Adeployed) - See what others have built
- [Smithery Examples](https://github.com/smithery-ai/mcp-servers) - MCP servers built by the team at Smithery
- [Advanced Configuration](https://smithery.ai/docs/config) - Environment variables, secrets, and more

**Join the Community:**
- [Smithery Discord](https://discord.gg/4H3bj5Rn9d) - Get help and share your servers
- [Smithery Server Requests](https://github.com/smithery-ai/rfm/discussions) - Want a server that's not available yet? Ask the community to build it!

