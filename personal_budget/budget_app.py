import argparse
import os
from datetime import date
from decimal import Decimal
from rich.text import Text
from textual.app import App, ComposeResult
from textual import on, work
from textual.reactive import reactive
from textual.containers import Container
from textual.containers import Horizontal
from textual.containers import Grid
from textual.message import Message
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

    def compose(self) -> ComposeResult:
        yield Label("", classes="modal-title-before")
        yield Label("Update Entry", classes="modal-title")
        with Grid(id="update-entry-form"):
            yield Label("Description:")
            yield Input(value=self.entry.description, id="entry_description")

            yield Label("Amount:")
            yield Input(value=str(self.entry.amount), id="entry_amount")

            yield Label("Category:")
            yield Input(value=str(self.entry.category), id="entry_category")

            yield Label("Recurrence:")
            with RadioSet(id="entry_recurrence"):
                for rt in RecurrenceType:
                    yield RadioButton(
                        rt.name,
                        value=rt == self.entry.recurrence.type,
                    )

            yield Label("Date:")
            yield Input(value=str(self.entry.recurrence.start_date), id="entry_date")

            # TODO: only show this if recurrence is MONTHLY
            yield Label("Every X months?")
            yield Input(value=str(self.entry.recurrence.every), id="entry_every")

            yield Button("Save", id="entry_save", variant="primary")
            yield Button("Cancel", id="entry_cancel")

    def _get_values(self):
        return {
            "description": self.query_one("#entry_description", Input).value,
            "amount": Decimal(self.query_one("#entry_amount", Input).value),
            "category": self.query_one("#entry_category", Input).value,
            "recurrence_type": RecurrenceType[
                str(
                    self.query_one("#entry_recurrence", RadioSet).pressed_button.label
                ).upper()
            ],
            "start_date": date.fromisoformat(self.query_one("#entry_date", Input).value),
            "every": int(self.query_one("#entry_every", Input).value),
        }

    @on(Button.Pressed, "#entry_save")
    def on_save(self, _) -> None:
        values = self._get_values()
        entry = FinancialEntry(
            description=values["description"],
            amount=values["amount"],
            category=values["category"],
            type=self.entry.type,
            recurrence=Recurrence(
                type=values["recurrence_type"],
                start_date=values["start_date"],
                every=values["every"],
            ),
        )
        self.dismiss(entry)

    @on(Button.Pressed, "#entry_cancel")
    def on_cancel(self, _) -> None:
        self.dismiss(None)


class FinancialEntriesScreen(Screen):
    SUB_TITLE = "Managing entries"

    def __init__(self, state: FinancialState, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state

    def compose(self) -> ComposeResult:
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

    @work
    @on(DataTable.RowSelected, "#expenses")
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # TODO: check if there is a surer way of mapping the row to the entry
        entry = self.state.expense_entries[event.cursor_row]
        result = await self.app.push_screen_wait(UpdateFinancialEntryModal(entry))
        if result:
            # TODO: update the entry in the state and refresh the table
            self.notify(f"Updated entry {result.description}", title="Entry updated")


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

    def compose(self) -> ComposeResult:
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
