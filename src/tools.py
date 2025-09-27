import os
import sqlite3
from db import init_db

# Sqlite DB Path
DB_PATH = os.path.join(os.path.dirname(__file__), "expense.db")

# Init DB if not exists 
init_db(DB_PATH)

def register_tools(mcp):
    """Register all expense tracking tools with the MCP server."""
    
    @mcp.tool()
    def add_expense(date, amount, category, subcategory="", note=""):
        '''Add a new expense entry to the database.'''
        with sqlite3.connect(DB_PATH) as c:
            cur = c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            return {"status": "ok", "id": cur.lastrowid}