from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "expense-tracker-secret"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            expense_date TEXT,
            category TEXT,
            user_id INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(expenses)")
    columns = [row[1] for row in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER DEFAULT 0")
        conn.commit()
    conn.close()


create_database()


def login_required(view):
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


def authenticate_user(username, password):
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        return user
    return None


@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = authenticate_user(username, password)

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    return login()


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            return render_template("register.html", error="Please fill all fields")

        hashed_password = generate_password_hash(password)
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users(username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("register.html", error="Username or email already exists")
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/register_user", methods=["POST"])
def register_user():
    return register()


@app.route("/home")
@login_required
def home():
    conn = get_db()
    cursor = conn.cursor()
    expenses = cursor.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()

    total = sum(expense["amount"] for expense in expenses)
    return render_template(
        "index.html",
        expenses=expenses,
        username=session["username"],
        total=round(total, 2),
    )


@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title", "").strip()
    amount = request.form.get("amount", "")
    expense_date = request.form.get("expense_date", "")
    category = request.form.get("category", "")

    if title and amount and expense_date and category:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses(title, amount, expense_date, category, user_id) VALUES (?, ?, ?, ?, ?)",
            (title, amount, expense_date, category, session["user_id"]),
        )
        conn.commit()
        conn.close()

    return redirect(url_for("home"))


@app.route("/edit_expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    conn = get_db()
    cursor = conn.cursor()
    expense = cursor.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    ).fetchone()

    if not expense:
        conn.close()
        return redirect(url_for("home"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount = request.form.get("amount", "")
        expense_date = request.form.get("expense_date", "")
        category = request.form.get("category", "")

        if title and amount and expense_date and category:
            cursor.execute(
                "UPDATE expenses SET title = ?, amount = ?, expense_date = ?, category = ? WHERE id = ? AND user_id = ?",
                (title, amount, expense_date, category, expense_id, session["user_id"]),
            )
            conn.commit()

        conn.close()
        return redirect(url_for("home"))

    conn.close()
    return render_template("edit_expense.html", expense=expense)


@app.route("/delete_expense/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("home"))


@app.route("/expenses")
@login_required
def expenses():
    conn = get_db()
    cursor = conn.cursor()
    expenses = cursor.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return render_template("expenses.html", expenses=expenses, username=session["username"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=5500)