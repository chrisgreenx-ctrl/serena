#!/usr/bin/env python3
"""
Render deployment wrapper for Serena MCP Server.
This script properly sets up the server with CORS middleware for public access on Render.
It includes comprehensive logging and error handling to diagnose startup issues.
"""
import os
import sys
import traceback
import time
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

# Configure unbuffered output immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

def print_log(message):
    """Print a log message with a timestamp and flush stdout."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    sys.stdout.flush()

def log_system_info():
    """Log system information for debugging."""
    try:
        import platform
        import psutil
        print_log(f"System: {platform.system()} {platform.release()}")
        print_log(f"Python: {sys.version}")

        mem = psutil.virtual_memory()
        print_log(f"Memory: Total={mem.total / (1024**2):.1f}MB, Available={mem.available / (1024**2):.1f}MB")

        disk = shutil.disk_usage("/")
        print_log(f"Disk: Total={disk.total / (1024**3):.1f}GB, Free={disk.free / (1024**3):.1f}GB")

        print_log(f"Current Working Directory: {os.getcwd()}")
        print_log(f"User: {os.getlogin() if hasattr(os, 'getlogin') else 'unknown'}")

        # List contents of key directories
        print_log("Checking directory structure...")
        check_dirs = ["src", "src/serena", "src/serena/resources"]
        for d in check_dirs:
            p = Path(d)
            if p.exists():
                print_log(f"Directory {d} exists. Contents: {[x.name for x in list(p.iterdir())[:10]]}")
            else:
                print_log(f"Directory {d} NOT FOUND")

    except Exception as e:
        print_log(f"Error gathering system info: {e}")

# Ensure the src directory is in the path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)
print_log(f"Added {src_path} to sys.path")

try:
    import uvicorn
    from starlette.applications import Starlette
    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from starlette.responses import Response

    # Attempt to import Serena modules
    print_log("Importing Serena modules...")
    from serena.mcp import SerenaMCPFactory
    print_log("Serena modules imported successfully.")

except Exception:
    print_log("CRITICAL: Failed to import dependencies.")
    traceback.print_exc()
    sys.exit(1)

def main():
    try:
        print_log("Serena MCP Server starting for Render deployment...")
        log_system_info()

        # Get port from environment variable (Render sets this to 10000 by default)
        port = int(os.environ.get("PORT", 10000))
        print_log(f"Configured PORT: {port}")

        # Create the Serena MCP factory
        print_log("Initializing SerenaMCPFactory...")
        factory = SerenaMCPFactory()

        # Create the MCP server
        # We disable dashboard and GUI logs as Render is headless
        print_log("Creating MCP server...")
        mcp_server = factory.create_mcp_server(
            host="0.0.0.0",
            port=port,
            enable_web_dashboard=False,
            enable_gui_log_window=False,
            log_level="INFO"
        )
        print_log("MCP server created.")

        # Get the Starlette app with streamable HTTP transport
        print_log("Creating streamable HTTP app...")
        mcp_app = mcp_server.streamable_http_app()

        # Define a lifespan context manager that ensures the MCP server tools are initialized
        @asynccontextmanager
        async def lifespan(app):
            print_log("Entering application lifespan...")
            try:
                # This calls _set_mcp_tools and ensures the agent is ready
                async with factory.server_lifespan(mcp_server):
                    print_log("Serena agent tools registered successfully.")
                    yield
            except Exception as e:
                print_log(f"Error during lifespan startup: {e}")
                traceback.print_exc()
                raise
            finally:
                print_log("Exiting application lifespan.")

        # Create a root Starlette app that manages the lifespan
        print_log("Creating root Starlette app...")
        root_app = Starlette(lifespan=lifespan)

        # Add a simple health check endpoint
        async def health_check(request):
            return Response("OK")

        root_app.add_route("/health", health_check, methods=["GET"])
        print_log("Health check route added at /health")

        # Mount the MCP app at the root
        # Note: We add the health route before mounting so it takes precedence
        root_app.mount("/", mcp_app)
        print_log("MCP app mounted at /")

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
            if response.status_code != 200 and request.url.path != "/health":
                 print_log(f"{request.method} {request.url.path} - {response.status_code}")
            return response

        print_log(f"Starting uvicorn on 0.0.0.0:{port}")
        uvicorn.run(root_app, host="0.0.0.0", port=port, log_level="info")

    except Exception:
        # Catch any startup errors and print the traceback
        print_log("CRITICAL ERROR: Application exited with exception.")
        traceback.print_exc()

        # Sleep to allow logs to be flushed and captured by Render
        print_log("Sleeping for 30 seconds to allow log capture...")
        time.sleep(30)
        sys.exit(1)

if __name__ == "__main__":
    main()
