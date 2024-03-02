import argparse
from datetime import date
from decimal import Decimal
from rich.text import Text
from textual.app import App
from textual.containers import Container
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import DataTable
from textual.widgets import Button
from textual.widgets import Label
from textual.widgets import Select
from textual import events
from personal_budget.state import (
    EntryType,
    FinancialEntry,
    FinancialState,
    Recurrence,
    RecurrenceType,
)


class BudgetApp(App):
    CSS_PATH = "style.css"

    def __init__(self, state_file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = (
            FinancialState.from_json_file(state_file) if state_file else FinancialState()
        )

    def compose(self):
        yield Header()
        yield Footer()

        yield Label("Expenses", id="expenses_label")
        yield DataTable(id="expenses")

        yield Label("Income sources", id="income_label")
        yield DataTable(id="income")

        with Horizontal(id="actions"):
            yield Button("Add Expense", variant="primary")
            yield Button("Add Income Source", variant="primary")

    def _fill_entries_table(
        self, table: DataTable, entries: list[FinancialEntry]
    ) -> None:
        table.add_columns("Description", "Amount", "Category", "Recurrence")

        if not entries:
            table.add_row(Text("No entries yet", style="italic"))
            return

        for entry in entries:
            table.add_row(
                entry.description,
                f"€{entry.amount}",
                entry.category,
                entry.recurrence.description,
            )

    def on_mount(self) -> None:
        self._fill_entries_table(self.query_one("#expenses"), self.state.expense_entries)
        self._fill_entries_table(self.query_one("#income"), self.state.income_entries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", help="Load financial state from file", type=str, default=None
    )
    args = parser.parse_args()

    app = BudgetApp(state_file=args.input)
    app.run()
