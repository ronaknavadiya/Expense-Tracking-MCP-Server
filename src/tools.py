import sqlite3
from .db import init_db
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Sqlite DB Path
DB_PATH = Path(__file__).parent.parent / "expense.db"

# Init DB if not exists 
init_db(DB_PATH)

def register_tools(mcp):
    """Register all expense tracking tools with the MCP server"""
    
    # Test logging when tools are registered
    logger.info("=== Registering expense tracking tools ===")
    logger.debug(f"Database path: {DB_PATH}")
    logger.debug(f"Database exists: {DB_PATH.exists()}")
    
    @mcp.tool()
    def add_expense(date, amount, category, subcategory="", note=""):
        '''Add a new expense entry to the database.'''
        logger.debug(f"add_expense called: {amount} for {category} on {date}")
        logger.debug(f"Connecting to database at: {DB_PATH}")
        
        try:
            with sqlite3.connect(DB_PATH) as c:
                cur = c.execute(
                    "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                    (date, amount, category, subcategory, note)
                )
                expense_id = cur.lastrowid
                logger.info(f"Successfully added expense with ID: {expense_id}")
                return {"status": "ok", "id": expense_id}
        except Exception as e:
            logger.error(f"Error adding expense: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def get_all_expenses():
        """Retrieve all expenses from the database"""
        logger.debug("=== get_all_expenses called ===")
        logger.debug(f"Connecting to database at: {DB_PATH}")
        logger.debug(f"Database file exists: {DB_PATH.exists()}")
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                
                # Check if table exists
                table_check = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
                ).fetchone()
                logger.debug(f"Table 'expenses' exists: {table_check is not None}")
                
                if not table_check:
                    logger.error("Table 'expenses' does not exist!")
                    return {"status": "error", "message": "Table 'expenses' not found"}
                
                cur = conn.execute("SELECT * FROM expenses ORDER BY date DESC")
                expenses = [dict(row) for row in cur.fetchall()]
                
                logger.info(f"Successfully retrieved {len(expenses)} expenses")
                logger.debug("=== get_all_expenses completed ===")
                
                return {"status":"Ok", "expenses":expenses}
                
        except Exception as e:
            logger.error(f"Error retrieving expenses: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    logger.info("=== All tools registered successfully ===")

    @mcp.tool()
    def get_expenses_by_category(category):
        '''Retrieve expenses filtered by category.'''
        with sqlite3.connect(DB_PATH) as c:
            c.row_factory = sqlite3.Row
            cur = c.execute("SELECT * FROM expenses WHERE category = ? ORDER BY date DESC", (category,))
            expenses = [dict(row) for row in cur.fetchall()]
            return {"status": "ok", "expenses": expenses}

    @mcp.tool()
    def get_expenses_by_date_range(start_date, end_date):
        '''Retrieve expenses within a date range.'''
        with sqlite3.connect(DB_PATH) as c:
            c.row_factory = sqlite3.Row
            cur = c.execute(
                "SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC", 
                (start_date, end_date)
            )
            expenses = [dict(row) for row in cur.fetchall()]
            return {"status": "ok", "expenses": expenses}