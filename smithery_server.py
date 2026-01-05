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

    # Step 2: Revert to Standard CORSMiddleware
    # We add this first so it wraps the application directly.
    # Subsequent middlewares (like logging) will wrap this one.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",  # Allows all origins dynamically
        allow_credentials=True,
        allow_methods=["*"],      # Allows all methods (GET, POST, PUT, DELETE, OPTIONS, HEAD)
        allow_headers=["*"],      # Allows all headers
        expose_headers=["*"],     # Exposes all headers to the browser
    )
    
    # Step 1: Diagnostics (Crucial)
    # Add a simple logging middleware at the very top of the stack (before CORS)
    # By adding it AFTER CORSMiddleware (using @app.middleware), it wraps the existing stack,
    # so it executes BEFORE CORSMiddleware on the incoming request.
    @app.middleware("http")
    async def log_request(request: Request, call_next):
        print("--- Incoming Request Diagnostics ---")
        print(f"Method: {request.method}")
        print(f"Path: {request.url.path}")
        print(f"Origin Header: {request.headers.get('origin', 'N/A')}")
        print(f"Host Header: {request.headers.get('host', 'N/A')}")
        print(f"Access-Control-Request-Method: {request.headers.get('access-control-request-method', 'N/A')}")
        print(f"Access-Control-Request-Headers: {request.headers.get('access-control-request-headers', 'N/A')}")
        print("------------------------------------")

        response = await call_next(request)
        return response
    
    print(f"Listening on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
