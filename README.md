# Personal Finance Manager

A simple, cross‑platform personal finance application written in Python.  It runs entirely on your local machine and requires nothing more than a modern version of Python with Tkinter and Matplotlib.  The application lets you record income and expenses, assign them to categories, set budgets and visualise your financial data with charts.  Everything is stored in a small SQLite database so your data remains private and portable.

## Features

Budgeting tools commonly focus on three core capabilities: tracking expenses, categorising spending and helping users set and monitor financial goals【191475796889102†L140-L152】.  This project implements those essential features and more:

* **Record transactions:** add income or expense entries with a date, category, description and amount.  Transactions are saved to an SQLite database for persistence.
* **Manage budgets:** set monthly budget amounts for your spending categories.  Budgets can be added, updated or deleted at any time.
* **View summaries:** see total income, total expenses and your current net balance at a glance.  Keeping all of your income, expenses and goals in one place reduces the complexity of managing money【191475796889102†L240-L244】.
* **Visualise your spending:** generate colour‑coded charts to spot spending patterns and discover opportunities to save.  A pie chart shows how your expenses are distributed across categories, and a bar chart compares income and expenses by month.  User‑friendly interfaces and visual aids like charts make budget apps quicker and less stressful to navigate【191475796889102†L205-L209】.
* **Custom categories:** create as many categories as you need to tailor the tracker to your lifestyle.  The ability to customise categories and spending limits is a hallmark of good budgeting tools【191475796889102†L213-L218】.

## Requirements

* Python 3.8 or later
* The Tkinter GUI library (bundled with most Python distributions)
* [Matplotlib](https://matplotlib.org/) for charting

Install the Python dependencies with pip:

```bash
pip install -r requirements.txt
```

## Running the application

From a command prompt in the project directory:

```bash
python app.py
```

This will create a window titled **“Personal Finance Manager”** with four tabs:

1. **Transactions:** add or delete income/expense entries.  Each entry stores the date (`YYYY‑MM‑DD`), type (Income or Expense), category, optional description and amount.
2. **Budgets:** assign monthly budget amounts to categories.  Budgets can be updated or removed.
3. **Summary:** view your total income, total expenses and net balance.
4. **Charts:** view a pie chart of expenses by category or a bar chart comparing monthly income and expenses.

On first run the program creates a database file called `finance.db` in the current directory.  If you ever want to start over, simply delete this file (though that will also delete all recorded transactions and budgets).

## Roadmap

This is a foundational version of a personal finance tracker.  Modern budget apps offer additional capabilities such as automatic bank account integration, subscription tracking and goal progress bars【191475796889102†L232-L236】.  Future enhancements might include recurring transactions, import/export of CSV files, notifications when spending nears a budget limit and more sophisticated analytics.

## Contributing

Pull requests are welcome!  If you have suggestions for additional features or improvements, please open an issue or submit a PR.
