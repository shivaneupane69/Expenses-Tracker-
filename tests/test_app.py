import importlib
import os
import tempfile
import unittest
import app as app_module


class ExpenseTrackerTests(unittest.TestCase):
    def setUp(self):
        self.db_path = os.path.join(tempfile.gettempdir(), 'expense-tracker-test.db')
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.environ['EXPENSES_DB'] = self.db_path
        self.app_module = importlib.reload(app_module)
        self.app = self.app_module.app
        self.app.config['TESTING'] = True
        self.app_module.create_database()
        self.client = self.app.test_client()

    def test_home_page_shows_add_form(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Expense', response.data)

    def test_add_expense_api_stores_and_returns_expenses(self):
        response = self.client.post('/add-expense', data={
            'title': 'Coffee',
            'amount': '4.50',
            'category': 'Food',
            'expense_date': '2026-07-01'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Coffee', response.data)
        self.assertIn(b'4.50', response.data)


if __name__ == '__main__':
    unittest.main()
