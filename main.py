
from fastmcp import FastMCP
from src.tools import register_tools
import logging
import sys

# Setup Debug configuration
DEBUG = True

def setup_logging():
    """Setup logging that doesn't interfere with MCP protocol"""
    if DEBUG:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('expense_tracker_debug.log'),
                logging.StreamHandler(sys.stderr)  # Use stderr instead of stdout
            ]
        )
    else:
        # Production: only log errors to file
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('expense_tracker_error.log')
            ]
        )


# Setup logging first
setup_logging()
# Create MCP server
mcp = FastMCP("ExpenseTracker")

# Register all tools from tools.py
register_tools(mcp)

if __name__ == "__main__":
    mcp.run()