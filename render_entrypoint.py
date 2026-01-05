#!/usr/bin/env python3
"""
Render deployment wrapper for Serena MCP Server.
This script properly sets up the server with CORS middleware for public access on Render.
"""
import os
import sys
import traceback
from contextlib import asynccontextmanager

# Ensure the src directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from serena.mcp import SerenaMCPFactory

def main():
    try:
        print("Serena MCP Server starting for Render deployment...")
        sys.stdout.flush()

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
        mcp_app = mcp_server.streamable_http_app()

        # Define a lifespan context manager that ensures the MCP server tools are initialized
        @asynccontextmanager
        async def lifespan(app):
            # This calls _set_mcp_tools and ensures the agent is ready
            async with factory.server_lifespan(mcp_server):
                yield

        # Create a root Starlette app that manages the lifespan
        root_app = Starlette(lifespan=lifespan)

        # Add a simple health check endpoint
        async def health_check(request):
            return Response("OK")

        root_app.add_route("/health", health_check, methods=["GET"])

        # Mount the MCP app at the root
        # Note: We add the health route before mounting so it takes precedence
        root_app.mount("/", mcp_app)

        # Add CORS Middleware to allow public access
        root_app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=".*",  # Allows all origins
            allow_credentials=True,
            allow_methods=["*"],      # Allows all methods
            allow_headers=["*"],      # Allows all headers
        )

        # Optional: Add request logging for diagnostics
        @root_app.middleware("http")
        async def log_request(request: Request, call_next):
            response = await call_next(request)
            return response

        print(f"Listening on 0.0.0.0:{port}")
        sys.stdout.flush()
        uvicorn.run(root_app, host="0.0.0.0", port=port, log_level="info")

    except Exception:
        # Catch any startup errors and print the traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
