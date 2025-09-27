
from fastmcp import FastMCP
from src.tools import register_tools

mcp = FastMCP("ExpenseTracker")

# Register all tools from tools.py
register_tools(mcp)

if __name__ == "__main__":
    mcp.run()