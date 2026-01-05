#!/usr/bin/env python3
"""
Render deployment wrapper for Serena MCP Server.
This script properly sets up the server with CORS middleware for public access on Render.
"""
import os
import sys
import logging
import traceback

# Configure logging immediately to catch any import or startup errors
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the src directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from serena.mcp import SerenaMCPFactory
except ImportError as e:
    logger.critical(f"Failed to import dependencies: {e}")
    sys.exit(1)

def main():
    try:
        logger.info("Serena MCP Server starting for Render deployment...")

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

        # Manually set up MCP tools because FastMCP's streamable_http_app() does not
        # execute the user-configured lifespan where tools are normally registered.
        # We replicate the logic from SerenaMCPFactory.server_lifespan here.
        logger.info("Manually initializing MCP tools...")
        openai_tool_compatible = factory.context.name in ["chatgpt", "codex", "oaicompat-agent"]
        factory._set_mcp_tools(mcp_server, openai_tool_compatible=openai_tool_compatible)
        logger.info("MCP tools initialized.")

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
        logger.debug(f"Request: {request.method} {request.url}")
            response = await call_next(request)
            return response

        logger.info(f"Listening on 0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
