#!/usr/bin/env python3
"""
Smithery deployment wrapper for Serena MCP Server.
This script properly sets up the server with CORS middleware for Smithery compatibility.
"""
import os
import sys

# Ensure the src directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import uvicorn
from starlette.middleware.cors import CORSMiddleware

from serena.mcp import SerenaMCPFactory
from serena.config.serena_config import SerenaConfig

def main():
    print("Serena MCP Server starting for Smithery deployment...")
    
    # Get port from environment variable (Smithery sets this to 8081)
    port = int(os.environ.get("PORT", 8081))
    
    # Create the Serena MCP factory with default settings
    factory = SerenaMCPFactory()
    
    # Create the MCP server
    mcp_server = factory.create_mcp_server(
        host="0.0.0.0",
        port=port,
        enable_web_dashboard=False,
        enable_gui_log_window=False,
        log_level="INFO"
    )
    
    # Get the Starlette app with streamable HTTP transport
    app = mcp_server.streamable_http_app()
    
    # Add CORS middleware for browser-based clients
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex='.*',
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
        allow_headers=["*", "mcp-protocol-version", "mcp-session-id"],
        expose_headers=["mcp-session-id", "mcp-protocol-version"],
        max_age=86400,
    )
    
    print(f"Listening on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
