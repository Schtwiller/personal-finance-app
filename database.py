"""
database.py
---------------

This module provides a simple SQLite-backed database for storing
transactions and budgets for the personal finance application.  It
exposes a ``Database`` class that encapsulates common operations such
as inserting, deleting and querying data.  The database is created
automatically if it does not already exist.  SQLite is used here for
its simplicity and because it requires no external server.

Tables
------

``transactions``
    Stores individual income and expense records.  Each row contains
    an auto-incrementing primary key, a date string (``YYYY-MM-DD``),
    a type (``Income`` or ``Expense``), a category, a free‑form
    description and a numeric amount.  Expenses should be entered as
    positive numbers; the application will interpret the ``type``
    column to determine whether the number represents income or
    expenditure.

``budgets``
    Stores user defined budgets for categories.  Each row contains
    an auto-incrementing primary key, a unique category name and the
    associated budget amount.  Budgets can be used to compare
    spending against planned amounts.

The methods provided by ``Database`` return raw data structures
appropriate for further processing or display in the user interface.
They intentionally avoid imposing any particular UI or formatting
logic on the caller.
"""

from __future__ import annotations

import sqlite3
from typing import List, Tuple, Optional


class Database:
    """Simple wrapper around an SQLite database for finance data."""

    def __init__(self, db_name: str = "finance.db") -> None:
        """
        Initialise the database connection and create tables if they
        do not already exist.

        :param db_name: Name of the SQLite database file to use.
        """
        # ``check_same_thread=False`` allows SQLite to be used from
        # multiple threads (e.g. Tkinter callbacks) without raising
        # exceptions.  Each thread still uses the same connection, so
        # transactions must be kept simple.
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self) -> None:
        """Create the necessary tables if they do not already exist."""
        cursor = self.conn.cursor()
        # Create the transactions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL
            )
            """
        )
        # Create the budgets table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL
            )
            """
        )
        self.conn.commit()

    def add_transaction(
        self, date: str, type_: str, category: str, description: str, amount: float
    ) -> None:
        """Insert a new transaction record.

        :param date: Date of the transaction in ``YYYY-MM-DD`` format.
        :param type_: Either ``Income`` or ``Expense``.
        :param category: Category for the transaction (e.g. ``Groceries``).
        :param description: Optional description of the transaction.
        :param amount: Monetary amount.  Should always be a positive value.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (date, type, category, description, amount) VALUES (?,?,?,?,?)",
            (date, type_, category, description, amount),
        )
        self.conn.commit()

    def get_transactions(self) -> List[Tuple[int, str, str, str, str, float]]:
        """Return all transactions sorted by date descending."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, date, type, category, description, amount FROM transactions ORDER BY date DESC, id DESC"
        )
        return cursor.fetchall()

    def delete_transaction(self, trans_id: int) -> None:
        """Delete a transaction by its ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id=?", (trans_id,))
        self.conn.commit()

    def add_budget(self, category: str, amount: float) -> None:
        """Insert or update a budget for a given category.

        Using ``INSERT OR REPLACE`` ensures that if a budget already
        exists for the category it will be updated; otherwise a new row
        will be created.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)",
            (category, amount),
        )
        self.conn.commit()

    def get_budgets(self) -> List[Tuple[int, str, float]]:
        """Return all budget entries."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, category, amount FROM budgets ORDER BY category")
        return cursor.fetchall()

    def delete_budget(self, budget_id: int) -> None:
        """Delete a budget entry by its ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM budgets WHERE id=?", (budget_id,))
        self.conn.commit()

    def get_summary(self) -> Tuple[float, float, float]:
        """
        Compute the total income, total expenses and net balance.

        :returns: A tuple ``(total_income, total_expense, net_balance)``.
        """
        cursor = self.conn.cursor()
        # Sum of incomes
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
        total_income = cursor.fetchone()[0] or 0.0
        # Sum of expenses
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
        total_expense = cursor.fetchone()[0] or 0.0
        # Net balance (income minus expenses)
        return total_income, total_expense, total_income - total_expense

    def get_expenses_by_category(self) -> List[Tuple[str, float]]:
        """
        Aggregate total expenses by category.

        :returns: A list of tuples ``(category, total_amount)`` sorted by
            total amount descending.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT category, SUM(amount) FROM transactions WHERE type='Expense' GROUP BY category ORDER BY SUM(amount) DESC"
        )
        return cursor.fetchall()

    def get_monthly_summary(self) -> List[Tuple[str, float, float]]:
        """
        Compute monthly income and expense totals.

        :returns: A list of tuples ``(month, income_total, expense_total)``
            where ``month`` is in ``YYYY-MM`` format.  The list is
            ordered chronologically by month.
        """
        cursor = self.conn.cursor()
        # SQLite does not have a native date type, so we store dates as
        # text (YYYY-MM-DD).  Using ``substr(date,1,7)`` extracts the
        # year and month for grouping.
        cursor.execute(
            """
            SELECT substr(date, 1, 7) AS month,
                   SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) AS income_total,
                   SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) AS expense_total
            FROM transactions
            GROUP BY month
            ORDER BY month
            """
        )
        return cursor.fetchall()

    def get_all_categories(self) -> List[str]:
        """
        Return a sorted list of all categories found in the budgets and
        transactions tables.  Categories are deduplicated and
        transformed to title case for nicer display.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM transactions")
        trans_cats = {row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT DISTINCT category FROM budgets")
        budget_cats = {row[0] for row in cursor.fetchall()}
        categories = {c for c in trans_cats.union(budget_cats) if c}
        # Sort alphabetically ignoring case
        return sorted(categories, key=lambda s: s.lower())

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self.conn.close()