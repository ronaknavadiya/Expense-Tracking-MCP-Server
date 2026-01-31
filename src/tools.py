import sqlite3
from .db import init_db
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Sqlite DB Path
DB_PATH = Path(__file__).parent.parent / "expense.db"

# Init DB if not exists 
init_db(DB_PATH)

# Log SQL query
def log_sql(statement):
    logger.debug(f"SQL executed: {statement}")

def register_tools(mcp):
    """Register all expense tracking tools with the MCP server"""
    
    # Test logging when tools are registered
    logger.info("=== Registering expense tracking tools ===")
    logger.debug(f"Database path: {DB_PATH}")
    logger.debug(f"Database exists: {DB_PATH.exists()}")
    
    @mcp.tool()
    def add_expense(date: str, amount: float, category: str, subcategory="", note=""):
        '''Add a new expense entry to the database.'''
        logger.debug(f"add_expense called: {amount} for {category} on {date}")
        logger.debug(f"Connecting to database at: {DB_PATH}")
        
        try:
            with sqlite3.connect(DB_PATH) as c:
                cur = c.execute(
                    "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                    (date.lower(), amount, category.lower(), subcategory.lower(), note.lower())
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
    def get_expenses_by_category(category: str):
        '''Retrieve expenses filtered by category.'''
        logger.debug("=== get_expenses_by_category called ===")
        logger.debug(f"Connecting to database at: {DB_PATH}")
        logger.debug(f"Database file exists: {DB_PATH.exists()}")
        with sqlite3.connect(DB_PATH) as c:
            c.row_factory = sqlite3.Row
            cur = c.execute("SELECT * FROM expenses WHERE category = ? ORDER BY date DESC", (category.lower()))
            expenses = [dict(row) for row in cur.fetchall()]
            return {"status": "ok", "expenses": expenses}

    @mcp.tool()
    def get_expenses_by_date_range(start_date: str, end_date: str):
        '''Retrieve expenses within a date range.'''
        logger.debug("=== get_expenses_by_date_range called ===")
        logger.debug(f"Connecting to database at: {DB_PATH}")
        logger.debug(f"Database file exists: {DB_PATH.exists()}")
        with sqlite3.connect(DB_PATH) as c:
            c.row_factory = sqlite3.Row
            cur = c.execute(
                "SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC", 
                (start_date.lower(), end_date.lower())
            )
            expenses = [dict(row) for row in cur.fetchall()]
            return {"status": "ok", "expenses": expenses}
        
    @mcp.tool()
    def delete_expense_by_date_and_title(date:str, title:str):
        ''' Delete expense by date and title '''
        with sqlite3.connect(DB_PATH) as conn:
            conn.set_trace_callback(log_sql)
            cur = conn.cursor()
            cur.execute("Delete FROM expenses WHERE date = ? AND note = ?", (date.lower() , title.lower()))
            deleted_rows = cur.rowcount
            conn.commit()
            logger.debug(f"{deleted_rows} rows have been deleted")
            return {"status":"ok", "deleted_rows": deleted_rows}

    # Analytics & Reporting Tools    
    @mcp.tool()
    def get_expense_summary(period: str = "all", category: str = None):
        '''Get expense summary with total spending. Period can be "all", "monthly", "yearly", or specific month/year.'''
        logger.debug(f"=== get_expense_summary called: period={period}, category={category} ===")
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                # Build query based on parameters
                base_query = "SELECT SUM(amount) as total, COUNT(*) as count, AVG(amount) as average"
                where_conditions = []
                params = []
                
                if category:
                    where_conditions.append("category = ?")
                    params.append(category.lower())
                
                if period == "monthly":
                    where_conditions.append("strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
                elif period == "yearly":
                    where_conditions.append("strftime('%Y', date) = strftime('%Y', 'now')")
                elif period != "all":
                    # Assume it's a specific month in YYYY-MM format
                    where_conditions.append("strftime('%Y-%m', date) = ?")
                    params.append(period)
                
                if where_conditions:
                    query = f"{base_query} FROM expenses WHERE {' AND '.join(where_conditions)}"
                else:
                    query = f"{base_query} FROM expenses"
                
                cur.execute(query, params)
                result = cur.fetchone()
                
                # Get category breakdown if no specific category requested
                category_breakdown = None
                if not category:
                    category_query = "SELECT category, SUM(amount) as total, COUNT(*) as count FROM expenses"
                    if period == "monthly":
                        category_query += " WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"
                    elif period == "yearly":
                        category_query += " WHERE strftime('%Y', date) = strftime('%Y', 'now')"
                    elif period != "all":
                        category_query += " WHERE strftime('%Y-%m', date) = ?"
                    
                    category_query += " GROUP BY category ORDER BY total DESC"
                    
                    cur.execute(category_query, params if period not in ["monthly", "yearly", "all"] else [])
                    category_breakdown = [dict(row) for row in cur.fetchall()]
                
                return {
                    "status": "ok",
                    "summary": {
                        "total_amount": result["total"] or 0,
                        "total_count": result["count"] or 0,
                        "average_amount": result["average"] or 0,
                        "period": period,
                        "category": category
                    },
                    "category_breakdown": category_breakdown
                }
                
        except Exception as e:
            logger.error(f"Error getting expense summary: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def get_monthly_spending(year: int = None, month: int = None):
        '''Get spending for a specific month. If no parameters provided, returns current month.'''
        logger.debug(f"=== get_monthly_spending called: year={year}, month={month} ===")
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                if year and month:
                    # Specific month requested
                    date_filter = f"{year:04d}-{month:02d}"
                    cur.execute("""
                        SELECT 
                            SUM(amount) as total,
                            COUNT(*) as count,
                            category,
                            SUM(amount) as category_total
                        FROM expenses 
                        WHERE strftime('%Y-%m', date) = ?
                        GROUP BY category
                        ORDER BY category_total DESC
                    """, (date_filter,))
                else:
                    # Current month
                    cur.execute("""
                        SELECT 
                            SUM(amount) as total,
                            COUNT(*) as count,
                            category,
                            SUM(amount) as category_total
                        FROM expenses 
                        WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
                        GROUP BY category
                        ORDER BY category_total DESC
                    """)
                
                results = cur.fetchall()
                total_spending = sum(row["category_total"] for row in results)
                
                return {
                    "status": "ok",
                    "month": f"{year:04d}-{month:02d}" if year and month else "current",
                    "total_spending": total_spending,
                    "total_transactions": sum(row["count"] for row in results),
                    "category_breakdown": [dict(row) for row in results]
                }
                
        except Exception as e:
            logger.error(f"Error getting monthly spending: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def get_category_totals(period: str = "all"):
        '''Get total spending by category for a specific period.'''
        logger.debug(f"=== get_category_totals called: period={period} ===")
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                base_query = """
                    SELECT 
                        category,
                        SUM(amount) as total,
                        COUNT(*) as count,
                        AVG(amount) as average,
                        MIN(amount) as min_amount,
                        MAX(amount) as max_amount
                    FROM expenses
                """
                
                where_clause = ""
                params = []
                
                if period == "monthly":
                    where_clause = " WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"
                elif period == "yearly":
                    where_clause = " WHERE strftime('%Y', date) = strftime('%Y', 'now')"
                elif period != "all":
                    where_clause = " WHERE strftime('%Y-%m', date) = ?"
                    params.append(period)
                
                query = f"{base_query}{where_clause} GROUP BY category ORDER BY total DESC"
                cur.execute(query, params)
                
                results = [dict(row) for row in cur.fetchall()]
                total_all_categories = sum(row["total"] for row in results)
                
                return {
                    "status": "ok",
                    "period": period,
                    "total_all_categories": total_all_categories,
                    "categories": results
                }
                
        except Exception as e:
            logger.error(f"Error getting category totals: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def get_spending_trends(period1: str, period2: str):
        '''Compare spending between two periods. Periods should be in YYYY-MM format or "current" for current month.'''
        logger.debug(f"=== get_spending_trends called: period1={period1}, period2={period2} ===")
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                # Get data for period 1
                if period1 == "current":
                    cur.execute("""
                        SELECT 
                            SUM(amount) as total,
                            COUNT(*) as count,
                            category,
                            SUM(amount) as category_total
                        FROM expenses 
                        WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
                        GROUP BY category
                    """)
                else:
                    cur.execute("""
                        SELECT 
                            SUM(amount) as total,
                            COUNT(*) as count,
                            category,
                            SUM(amount) as category_total
                        FROM expenses 
                        WHERE strftime('%Y-%m', date) = ?
                        GROUP BY category
                    """, (period1,))
                
                period1_data = {row["category"]: dict(row) for row in cur.fetchall()}
                
                # Get data for period 2
                if period2 == "current":
                    cur.execute("""
                        SELECT 
                            SUM(amount) as total,
                            COUNT(*) as count,
                            category,
                            SUM(amount) as category_total
                        FROM expenses 
                        WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
                        GROUP BY category
                    """)
                else:
                    cur.execute("""
                        SELECT 
                            SUM(amount) as total,
                            COUNT(*) as count,
                            category,
                            SUM(amount) as category_total
                        FROM expenses 
                        WHERE strftime('%Y-%m', date) = ?
                        GROUP BY category
                    """, (period2,))
                
                period2_data = {row["category"]: dict(row) for row in cur.fetchall()}
                
                # Calculate trends
                all_categories = set(period1_data.keys()) | set(period2_data.keys())
                trends = []
                
                for category in all_categories:
                    p1_data = period1_data.get(category, {"category_total": 0, "count": 0})
                    p2_data = period2_data.get(category, {"category_total": 0, "count": 0})
                    
                    p1_total = p1_data["category_total"] or 0
                    p2_total = p2_data["category_total"] or 0
                    
                    change_amount = p2_total - p1_total
                    change_percentage = (change_amount / p1_total * 100) if p1_total > 0 else 0
                    
                    trends.append({
                        "category": category,
                        "period1_total": p1_total,
                        "period2_total": p2_total,
                        "change_amount": change_amount,
                        "change_percentage": round(change_percentage, 2)
                    })
                
                # Sort by absolute change amount
                trends.sort(key=lambda x: abs(x["change_amount"]), reverse=True)
                
                total_p1 = sum(period1_data.values(), {}).get("total", 0) or sum(row["category_total"] for row in period1_data.values())
                total_p2 = sum(period2_data.values(), {}).get("total", 0) or sum(row["category_total"] for row in period2_data.values())
                
                return {
                    "status": "ok",
                    "period1": period1,
                    "period2": period2,
                    "total_change": total_p2 - total_p1,
                    "total_change_percentage": round(((total_p2 - total_p1) / total_p1 * 100) if total_p1 > 0 else 0, 2),
                    "trends": trends
                }
                
        except Exception as e:
            logger.error(f"Error getting spending trends: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def get_top_categories(limit: int = 5, period: str = "all"):
        '''Get top spending categories. Limit defaults to 5, period can be "all", "monthly", "yearly", or YYYY-MM.'''
        logger.debug(f"=== get_top_categories called: limit={limit}, period={period} ===")
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                base_query = """
                    SELECT 
                        category,
                        SUM(amount) as total,
                        COUNT(*) as count,
                        AVG(amount) as average
                    FROM expenses
                """
                
                where_clause = ""
                params = []
                
                if period == "monthly":
                    where_clause = " WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"
                elif period == "yearly":
                    where_clause = " WHERE strftime('%Y', date) = strftime('%Y', 'now')"
                elif period != "all":
                    where_clause = " WHERE strftime('%Y-%m', date) = ?"
                    params.append(period)
                
                query = f"{base_query}{where_clause} GROUP BY category ORDER BY total DESC LIMIT ?"
                params.append(limit)
                
                cur.execute(query, params)
                results = [dict(row) for row in cur.fetchall()]
                
                return {
                    "status": "ok",
                    "period": period,
                    "limit": limit,
                    "top_categories": results
                }
                
        except Exception as e:
            logger.error(f"Error getting top categories: {e}")
            return {"status": "error", "message": str(e)}