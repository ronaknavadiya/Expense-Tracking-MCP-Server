import sqlite3

def add_expense(mcp, DB_PATH, date, amount, category, subcategory="", note=""):
    """ Add a new expense entry to the database """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )

    return {"status":"Ok", "id":conn.lastrowid}

