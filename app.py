from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# Create database
def create_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        expense_date TEXT,
        category TEXT
    )
    """)

    conn.commit()
    conn.close()

create_database()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add", methods=["POST"])
def add():

    title = request.form["title"]
    amount = request.form["amount"]
    expense_date = request.form["expense_date"]
    category = request.form["category"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO expenses(title,amount,expense_date,category)
    VALUES(?,?,?,?)
    """, (title, amount, expense_date, category))

    conn.commit()
    conn.close()

    return redirect("/expenses")


@app.route("/expenses")
def expenses():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expenses")

    data = cursor.fetchall()

    conn.close()

    return render_template("expenses.html", expenses=data)


if __name__ == "__main__":
    app.run(debug=True)