"""
app.py
------

This file defines the graphical user interface for the personal
finance manager.  It uses Tkinter for the windowing and widgets and
matplotlib for charting.  Data persistence is handled by the
``Database`` class from ``database.py``.

The application is organised into four tabs via a ``ttk.Notebook``:

1. **Transactions** – A form for adding income and expense entries
   and a list showing existing transactions.  The user can add a
   transaction by entering a date, selecting a type (income or
   expense), specifying a category, adding an optional description and
   an amount.  Transactions can be deleted via a button.
2. **Budgets** – Manage category budgets.  Users can add or update
   budgets for specific categories.  Budgets are displayed in a
   table with the ability to delete individual entries.
3. **Summary** – Presents aggregate statistics for total income,
   expenses and the resulting balance.  A refresh button updates the
   figures.
4. **Charts** – Visualise spending and earning patterns.  Two charts
   are available: a pie chart showing expenses by category and a
   monthly bar chart comparing income and expenses.  Selecting a
   chart replaces the previous figure within the tab.

Running the application
~~~~~~~~~~~~~~~~~~~~~~~

The program can be launched directly with Python:

.. code-block:: bash

    python app.py

Make sure that the required dependencies are installed (see
``requirements.txt``) and that a display environment is available if
running on a headless system (e.g. via ``xvfb``).  The GUI will
create or open an SQLite database file named ``finance.db`` in the
current working directory.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional

import matplotlib

# Use the TkAgg backend so that figures embed correctly in Tkinter.
matplotlib.use("TkAgg")  # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from database import Database


class FinanceApp:
    """Main application class encapsulating the Tkinter GUI."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Personal Finance Manager")
        self.db = Database()
        # Configure root window minimum size
        self.root.geometry("900x600")

        # Create the notebook (tab control)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Tabs
        self.tab_transactions = ttk.Frame(self.notebook)
        self.tab_budgets = ttk.Frame(self.notebook)
        self.tab_summary = ttk.Frame(self.notebook)
        self.tab_charts = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_transactions, text="Transactions")
        self.notebook.add(self.tab_budgets, text="Budgets")
        self.notebook.add(self.tab_summary, text="Summary")
        self.notebook.add(self.tab_charts, text="Charts")

        # Build each tab's UI
        self.build_transactions_tab()
        self.build_budgets_tab()
        self.build_summary_tab()
        self.build_charts_tab()

        # Populate initial data
        self.refresh_transactions()
        self.refresh_budgets()
        self.refresh_summary()

    # ------------------------------------------------------------------
    # Transactions tab
    # ------------------------------------------------------------------
    def build_transactions_tab(self) -> None:
        """Create widgets for the transactions tab."""
        frame_form = ttk.LabelFrame(self.tab_transactions, text="Add Transaction")
        frame_form.pack(fill="x", padx=10, pady=10)

        # Date input
        ttk.Label(frame_form, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_date = ttk.Entry(frame_form)
        self.entry_date.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        # Default to today's date
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Type combobox
        ttk.Label(frame_form, text="Type:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.combo_type = ttk.Combobox(frame_form, values=["Income", "Expense"], state="readonly")
        self.combo_type.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.combo_type.set("Expense")

        # Category entry
        ttk.Label(frame_form, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_category = ttk.Entry(frame_form)
        self.entry_category.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Description entry
        ttk.Label(frame_form, text="Description:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.entry_description = ttk.Entry(frame_form)
        self.entry_description.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Amount entry
        ttk.Label(frame_form, text="Amount:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_amount = ttk.Entry(frame_form)
        self.entry_amount.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Add button
        btn_add = ttk.Button(frame_form, text="Add Transaction", command=self.add_transaction)
        btn_add.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        # Treeview for transactions
        columns = ("id", "date", "type", "category", "description", "amount")
        self.tree_transactions = ttk.Treeview(
            self.tab_transactions,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=12,
        )
        # Define headings
        self.tree_transactions.heading("id", text="ID")
        self.tree_transactions.heading("date", text="Date")
        self.tree_transactions.heading("type", text="Type")
        self.tree_transactions.heading("category", text="Category")
        self.tree_transactions.heading("description", text="Description")
        self.tree_transactions.heading("amount", text="Amount")
        # Define column widths
        self.tree_transactions.column("id", width=40, anchor="center")
        self.tree_transactions.column("date", width=90)
        self.tree_transactions.column("type", width=80, anchor="center")
        self.tree_transactions.column("category", width=120)
        self.tree_transactions.column("description", width=200)
        self.tree_transactions.column("amount", width=100, anchor="e")

        self.tree_transactions.pack(fill="both", expand=True, padx=10, pady=10)

        # Delete button
        btn_delete = ttk.Button(self.tab_transactions, text="Delete Selected", command=self.delete_selected_transaction)
        btn_delete.pack(pady=(0, 10))

    def add_transaction(self) -> None:
        """Validate input and add a transaction to the database."""
        date_str = self.entry_date.get().strip()
        type_ = self.combo_type.get()
        category = self.entry_category.get().strip()
        description = self.entry_description.get().strip()
        amount_str = self.entry_amount.get().strip()

        # Basic validation
        if not date_str:
            messagebox.showerror("Input Error", "Date is required.")
            return
        try:
            # Validate format; will raise ValueError if invalid
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Date must be in YYYY-MM-DD format.")
            return
        if not category:
            messagebox.showerror("Input Error", "Category is required.")
            return
        if not amount_str:
            messagebox.showerror("Input Error", "Amount is required.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a positive number.")
            return

        # Insert into database
        try:
            self.db.add_transaction(date_str, type_, category, description, amount)
        except Exception as exc:
            messagebox.showerror("Database Error", f"Failed to add transaction: {exc}")
            return

        # Clear input fields for convenience
        self.entry_category.delete(0, tk.END)
        self.entry_description.delete(0, tk.END)
        self.entry_amount.delete(0, tk.END)
        # Optionally keep the date and type for next entry

        self.refresh_transactions()
        self.refresh_summary()
        messagebox.showinfo("Success", "Transaction added successfully.")

    def refresh_transactions(self) -> None:
        """Reload transactions from the database into the treeview."""
        # Clear existing items
        for item in self.tree_transactions.get_children():
            self.tree_transactions.delete(item)
        # Fetch and insert new rows
        for row in self.db.get_transactions():
            # Format amount to two decimal places
            formatted_amount = f"{row[5]:.2f}"
            self.tree_transactions.insert("", tk.END, values=(row[0], row[1], row[2], row[3], row[4], formatted_amount))

    def delete_selected_transaction(self) -> None:
        """Delete the transaction currently selected in the treeview."""
        selected = self.tree_transactions.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a transaction to delete.")
            return
        item = selected[0]
        values = self.tree_transactions.item(item, "values")
        trans_id = int(values[0])
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?")
        if confirm:
            try:
                self.db.delete_transaction(trans_id)
                self.refresh_transactions()
                self.refresh_summary()
            except Exception as exc:
                messagebox.showerror("Database Error", f"Failed to delete transaction: {exc}")

    # ------------------------------------------------------------------
    # Budgets tab
    # ------------------------------------------------------------------
    def build_budgets_tab(self) -> None:
        """Create widgets for the budgets tab."""
        frame_form = ttk.LabelFrame(self.tab_budgets, text="Add/Update Budget")
        frame_form.pack(fill="x", padx=10, pady=10)

        # Category
        ttk.Label(frame_form, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_budget_category = ttk.Entry(frame_form)
        self.entry_budget_category.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Amount
        ttk.Label(frame_form, text="Amount:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.entry_budget_amount = ttk.Entry(frame_form)
        self.entry_budget_amount.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Add/Update button
        btn_add_budget = ttk.Button(frame_form, text="Add/Update Budget", command=self.add_update_budget)
        btn_add_budget.grid(row=0, column=4, padx=5, pady=5, sticky="w")

        # Treeview for budgets
        columns = ("id", "category", "amount")
        self.tree_budgets = ttk.Treeview(
            self.tab_budgets,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=12,
        )
        self.tree_budgets.heading("id", text="ID")
        self.tree_budgets.heading("category", text="Category")
        self.tree_budgets.heading("amount", text="Amount")
        self.tree_budgets.column("id", width=40, anchor="center")
        self.tree_budgets.column("category", width=200)
        self.tree_budgets.column("amount", width=100, anchor="e")
        self.tree_budgets.pack(fill="both", expand=True, padx=10, pady=10)

        # Delete button
        btn_delete_budget = ttk.Button(self.tab_budgets, text="Delete Selected", command=self.delete_selected_budget)
        btn_delete_budget.pack(pady=(0, 10))

    def add_update_budget(self) -> None:
        """Validate input and add or update a budget entry."""
        category = self.entry_budget_category.get().strip()
        amount_str = self.entry_budget_amount.get().strip()
        if not category:
            messagebox.showerror("Input Error", "Category is required.")
            return
        if not amount_str:
            messagebox.showerror("Input Error", "Amount is required.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a positive number.")
            return
        try:
            self.db.add_budget(category, amount)
        except Exception as exc:
            messagebox.showerror("Database Error", f"Failed to add/update budget: {exc}")
            return
        # Clear inputs
        self.entry_budget_category.delete(0, tk.END)
        self.entry_budget_amount.delete(0, tk.END)
        self.refresh_budgets()
        messagebox.showinfo("Success", "Budget added/updated successfully.")

    def refresh_budgets(self) -> None:
        """Reload budget entries into the treeview."""
        for item in self.tree_budgets.get_children():
            self.tree_budgets.delete(item)
        for row in self.db.get_budgets():
            formatted_amount = f"{row[2]:.2f}"
            self.tree_budgets.insert("", tk.END, values=(row[0], row[1], formatted_amount))

    def delete_selected_budget(self) -> None:
        """Delete the selected budget entry."""
        selected = self.tree_budgets.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a budget to delete.")
            return
        item = selected[0]
        values = self.tree_budgets.item(item, "values")
        budget_id = int(values[0])
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this budget?")
        if confirm:
            try:
                self.db.delete_budget(budget_id)
                self.refresh_budgets()
            except Exception as exc:
                messagebox.showerror("Database Error", f"Failed to delete budget: {exc}")

    # ------------------------------------------------------------------
    # Summary tab
    # ------------------------------------------------------------------
    def build_summary_tab(self) -> None:
        """Create widgets for the summary tab."""
        frame = ttk.Frame(self.tab_summary)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Labels for totals
        ttk.Label(frame, text="Total Income:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.var_total_income = tk.StringVar(value="0.00")
        ttk.Label(frame, textvariable=self.var_total_income).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame, text="Total Expenses:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.var_total_expenses = tk.StringVar(value="0.00")
        ttk.Label(frame, textvariable=self.var_total_expenses).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame, text="Net Balance:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.var_net_balance = tk.StringVar(value="0.00")
        ttk.Label(frame, textvariable=self.var_net_balance).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Refresh button
        btn_refresh = ttk.Button(frame, text="Refresh", command=self.refresh_summary)
        btn_refresh.grid(row=3, column=0, columnspan=2, pady=10)

    def refresh_summary(self) -> None:
        """Update the totals displayed on the summary tab."""
        total_income, total_expense, net_balance = self.db.get_summary()
        self.var_total_income.set(f"{total_income:.2f}")
        self.var_total_expenses.set(f"{total_expense:.2f}")
        self.var_net_balance.set(f"{net_balance:.2f}")

    # ------------------------------------------------------------------
    # Charts tab
    # ------------------------------------------------------------------
    def build_charts_tab(self) -> None:
        """Create widgets for the charts tab."""
        frame_buttons = ttk.Frame(self.tab_charts)
        frame_buttons.pack(fill="x", padx=10, pady=10)

        btn_expense_chart = ttk.Button(
            frame_buttons,
            text="Expenses by Category",
            command=self.display_expense_by_category_chart,
        )
        btn_expense_chart.pack(side="left", padx=5)

        btn_monthly_chart = ttk.Button(
            frame_buttons,
            text="Monthly Income vs Expenses",
            command=self.display_monthly_summary_chart,
        )
        btn_monthly_chart.pack(side="left", padx=5)

        # Canvas area for charts
        self.chart_frame = ttk.Frame(self.tab_charts)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.current_canvas: Optional[FigureCanvasTkAgg] = None

    def _clear_chart(self) -> None:
        """Remove any existing matplotlib canvas from the chart frame."""
        if self.current_canvas is not None:
            self.current_canvas.get_tk_widget().destroy()
            self.current_canvas = None

    def display_expense_by_category_chart(self) -> None:
        """Display a pie chart of expenses grouped by category."""
        data = self.db.get_expenses_by_category()
        if not data:
            messagebox.showinfo("No Data", "There are no expenses to display.")
            return
        categories = [row[0] for row in data]
        amounts = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(6, 5), dpi=100)
        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=categories,
            autopct=lambda pct: f"{pct:.1f}%\n({amounts[categories.index(texts[i].get_text())]:.2f})" if pct > 0 else '',
            startangle=90,
        )
        ax.set_title("Expenses by Category")
        ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular

        self._show_chart(fig)

    def display_monthly_summary_chart(self) -> None:
        """Display a bar chart comparing monthly income and expenses."""
        data = self.db.get_monthly_summary()
        if not data:
            messagebox.showinfo("No Data", "There are no transactions to display.")
            return
        months = [row[0] for row in data]
        incomes = [row[1] for row in data]
        expenses = [row[2] for row in data]

        fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
        index = range(len(months))
        bar_width = 0.35
        ax.bar([i - bar_width / 2 for i in index], incomes, bar_width, label="Income", color="#4CAF50")
        ax.bar([i + bar_width / 2 for i in index], expenses, bar_width, label="Expense", color="#F44336")
        ax.set_xticks(list(index))
        ax.set_xticklabels(months, rotation=45)
        ax.set_ylabel("Amount")
        ax.set_title("Monthly Income vs Expenses")
        ax.legend()

        self._show_chart(fig)

    def _show_chart(self, fig) -> None:
        """Embed a matplotlib figure into the chart frame."""
        self._clear_chart()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.current_canvas = canvas


def main() -> None:
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()