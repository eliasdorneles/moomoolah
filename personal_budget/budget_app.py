import argparse
import os
from datetime import date
from decimal import Decimal
from rich.text import Text
from textual.app import App, ComposeResult
from textual import on
from textual.containers import Container
from textual.containers import Horizontal
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Input
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import DataTable
from textual.widgets import Button
from textual.widgets import Label
from textual.widgets import RadioButton
from textual.widgets import RadioSet
from textual.widgets import Select
from textual import events
from personal_budget.state import (
    EntryType,
    FinancialEntry,
    FinancialState,
    Recurrence,
    RecurrenceType,
)


class UpdateFinancialEntryModal(ModalScreen):
    SUB_TITLE = "Update entry"
    BINDINGS = [("escape", "app.pop_screen", "Cancel")]

    def __init__(self, entry: FinancialEntry, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entry = entry

    def compose(self):
        yield Label("", classes="modal-title-before")
        yield Label("Update Entry", classes="modal-title")
        with Grid(id="update-entry-form"):
            yield Label("Description:")
            yield Input(value=self.entry.description)

            yield Label("Amount:")
            yield Input(value=str(self.entry.amount))

            yield Label("Category:")
            yield Input(value=str(self.entry.category))

            yield Label("Recurrence:")
            with RadioSet(id="recurrence"):
                for rt in RecurrenceType:
                    yield RadioButton(
                        rt.name,
                        value=rt == self.entry.recurrence.type,
                    )

            yield Label("Date:")
            yield Input(value=str(self.entry.recurrence.start_date))

            # TODO: only show this if recurrence is MONTHLY
            yield Label("Every X months?")
            yield Input(value=str(self.entry.recurrence.every))

            yield Button("Save", id="save", variant="primary")
            yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#save")
    def on_save(self, event: Button.Pressed) -> None:
        # TODO: load values from grid and update entry
        pass


class FinancialEntriesScreen(Screen):
    SUB_TITLE = "Managing entries"

    def __init__(self, state: FinancialState, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state

    def compose(self):
        yield Header()
        yield Footer()

        yield Label("Expenses", id="expenses_label")
        yield DataTable(id="expenses", cursor_type="row")

        yield Label("Income sources", id="income_label")
        yield DataTable(id="income", cursor_type="row")

        with Horizontal(id="actions"):
            yield Button("Add Expense", variant="primary")
            yield Button("Add Income Source", variant="primary")

    def _fill_entries_table(
        self, table: DataTable, entries: list[FinancialEntry]
    ) -> None:
        table.add_columns("Description", "Amount", "Recurrence", "Category")

        if not entries:
            table.add_row(Text("No entries yet", style="italic"))
            return

        for entry in entries:
            table.add_row(
                entry.description,
                Text(f"€{entry.amount}", style="bold", justify="right"),
                entry.recurrence.description,
                entry.category,
            )

    def on_mount(self) -> None:
        self._fill_entries_table(
            self.query_one("#expenses", DataTable),
            self.state.expense_entries,
        )
        self._fill_entries_table(
            self.query_one("#income", DataTable),
            self.state.income_entries,
        )

    @on(DataTable.RowSelected, "#expenses")
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # TODO: check if there is a surer way of mapping the row to the entry
        entry = self.state.expense_entries[event.cursor_row]
        self.app.push_screen(UpdateFinancialEntryModal(entry))


class BudgetApp(App):
    TITLE = "Personal Budget Planner"
    CSS_PATH = "style.css"

    BINDINGS = [
        ("q", "save_and_quit", "Save and quit"),
        ("Q", "save_and_quit", "Save and quit"),
        ("ctrl+s", "save_state", "Save"),
        ("ctrl+S", "save_state", "Save"),
    ]

    def __init__(self, state_file, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if os.path.exists(state_file):
            self.state = FinancialState.from_json_file(state_file)
        else:
            # if file doesn't exist, create a new one
            self.state = FinancialState()
            self.state.to_json_file(state_file)
            self.notify(
                f"Created file {os.path.basename(state_file)}",
                title="Initialized state",
            )

        self.state_file = state_file

    def compose(self):
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        # TODO: if state has no entries, invite user to create a new one
        # TODO: if state has entrie, display the forecast for the next months,
        #       with option to manage entries
        self.push_screen(FinancialEntriesScreen(self.state))

    def action_save_state(self) -> None:
        # TODO: ask user where to save, if no state file was given
        self.state.to_json_file(self.state_file)
        self.notify(
            f"Written file {os.path.basename(self.state_file)}", title="Saved state"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "state_file", help="Financial state to load and/or save to", type=str
    )
    args = parser.parse_args()

    app = BudgetApp(state_file=args.state_file)
    app.run()
