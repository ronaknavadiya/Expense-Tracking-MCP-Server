from fastmcp import FastMCP
import os
import sqlite3
from db import init_db


mcp = FastMCP("ExpenseTracker")

# Sqlite DB Path
DB_PATH = os.path.join(os.path.dirname(__file__),"expense.db")

# Init DB if not exists 
init_db(DB_PATH)

# Tools

@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {"status": "ok", "id": cur.lastrowid}


if __name__ == "__main__":
    mcp.run()
