import os
import sqlite3
import unittest
import uuid

from app import app, create_database


class ExpenseTrackerTests(unittest.TestCase):
    def setUp(self):
        if os.path.exists("database.db"):
            os.remove("database.db")
        create_database()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_login_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Expense Tracker", response.data)

    def test_register_login_and_expense_flow(self):
        username = f"tester_{uuid.uuid4().hex[:6]}"
        response = self.client.post(
            "/register_user",
            data={
                "username": username,
                "email": f"{username}@example.com",
                "password": "secret123",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/login",
            data={"username": username, "password": "secret123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add Expense", response.data)

        response = self.client.post(
            "/add",
            data={
                "title": "Coffee",
                "amount": "4.50",
                "expense_date": "2026-07-01",
                "category": "Food",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Coffee", response.data)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        expense = cursor.execute(
            "SELECT id FROM expenses WHERE title = ?",
            ("Coffee",),
        ).fetchone()
        conn.close()
        self.assertIsNotNone(expense)
        expense_id = expense[0]

        response = self.client.post(
            f"/edit_expense/{expense_id}",
            data={
                "title": "Coffee Updated",
                "amount": "5.50",
                "expense_date": "2026-07-02",
                "category": "Food",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Coffee Updated", response.data)

        response = self.client.post(
            f"/delete_expense/{expense_id}",
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Coffee Updated", response.data)


if __name__ == "__main__":
    unittest.main()
