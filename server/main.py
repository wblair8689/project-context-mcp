"""
Main entry point for Project Context MCP Server
"""
import argparse
import logging
from pathlib import Path
from .base import UnifiedProjectContextServer


def main():
    """Main entry point for the server"""
    parser = argparse.ArgumentParser(description="Unified Project Context MCP Server")
    parser.add_argument("--project-root", 
                       default="/Users/williamblair/AI-Game-Evolution-Platform",
                       help="Root directory of the project")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="MCP transport method")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    try:
        server = UnifiedProjectContextServer(args.project_root)
        # Use logging instead of print to avoid interfering with JSON-RPC protocol
        logging.info(f"Starting Unified Project Context MCP Server")
        logging.info(f"Project Root: {args.project_root}")
        logging.info(f"Debug: {args.debug}")
        
        server.run_server(transport=args.transport)
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        if args.debug:
            import traceback
            logging.error(traceback.format_exc())


if __name__ == "__main__":
    main()
