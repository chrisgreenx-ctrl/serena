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
from starlette.requests import Request
from starlette.responses import Response

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
    
    # Manual CORS Middleware for Reflected Origin Strategy
    @app.middleware("http")
    async def manual_cors_middleware(request: Request, call_next):
        origin = request.headers.get("origin")
        print(f"Incoming Origin: {origin}")

        # Define common headers
        allow_origin = origin if origin else "*"
        allow_credentials = "true"
        allow_methods = "GET, POST, PUT, DELETE, OPTIONS, HEAD"
        # Explicitly list allowed headers instead of wildcard
        allow_headers = "Content-Type, Authorization, mcp-protocol-version, mcp-session-id"

        # Handle Preflight OPTIONS
        if request.method == "OPTIONS":
            response = Response(status_code=204)
            response.headers["Access-Control-Allow-Origin"] = allow_origin
            response.headers["Access-Control-Allow-Credentials"] = allow_credentials
            response.headers["Access-Control-Allow-Methods"] = allow_methods
            response.headers["Access-Control-Allow-Headers"] = allow_headers
            return response

        # Handle standard requests
        response = await call_next(request)

        # Reflect Origin
        response.headers["Access-Control-Allow-Origin"] = allow_origin
        response.headers["Access-Control-Allow-Credentials"] = allow_credentials
        response.headers["Access-Control-Allow-Methods"] = allow_methods
        response.headers["Access-Control-Allow-Headers"] = allow_headers

        return response
    
    print(f"Listening on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
