#!/usr/bin/env python3
"""
Render deployment wrapper for Serena MCP Server.
This script properly sets up the server with CORS middleware for public access on Render.
"""
import os
import sys

# Ensure the src directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from serena.mcp import SerenaMCPFactory

def main():
    print("Serena MCP Server starting for Render deployment...")

    # Get port from environment variable (Render sets this to 10000 by default)
    port = int(os.environ.get("PORT", 10000))

    # Create the Serena MCP factory
    factory = SerenaMCPFactory()

    # Create the MCP server
    # We disable dashboard and GUI logs as Render is headless
    mcp_server = factory.create_mcp_server(
        host="0.0.0.0",
        port=port,
        enable_web_dashboard=False,
        enable_gui_log_window=False,
        log_level="INFO"
    )

    # Get the Starlette app with streamable HTTP transport
    # Note: FastMCP provides this method to expose the underlying Starlette app
    app = mcp_server.streamable_http_app()

    # Add CORS Middleware to allow public access
    # We wrap the app with CORSMiddleware to handle cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],      # Allows all methods
        allow_headers=["*"],      # Allows all headers
    )

    # Optional: Add request logging for diagnostics
    @app.middleware("http")
    async def log_request(request: Request, call_next):
        response = await call_next(request)
        return response

    print(f"Listening on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
