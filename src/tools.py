import os
import sqlite3
from .db import init_db
from pathlib import Path

# Sqlite DB Path
# DB_PATH = os.path.join(os.path.dirname(__file__), "expense.db")
DB_PATH = Path(__file__).parent.parent / "expense.db"
# print("DB_PATH", DB_PATH)

# Init DB if not exists 
init_db(DB_PATH)

def register_tools(mcp):
    """Register all expense tracking tools with the MCP server"""
    
    @mcp.tool()
    def add_expense(date, amount, category, subcategory="", note=""):
        '''Add a new expense entry to the database.'''
        with sqlite3.connect(DB_PATH) as c:
            cur = c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            return {"status": "ok", "id": cur.lastrowid}

    @mcp.tool()
    def get_all_expenses():
        """Retrieve all expenses from the database"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM expenses ORDER BY date DESC")
            # print("curr ->" , cur)
            # for row in cur.fetchall():
            #     print(row) 
            expenses = [dict(row) for row in cur.fetchall()]
            return {"status":"Ok", "expenses":expenses}
