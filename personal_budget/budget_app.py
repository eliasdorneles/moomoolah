import argparse
import os
from datetime import date
from decimal import Decimal

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen, Screen
from textual.widgets import (Button, DataTable, Footer, Header, Input, Label,
                             RadioButton, RadioSet)

from personal_budget.state import (EntryType, FinancialEntry, FinancialState,
                                   MonthlyForecast, Recurrence, RecurrenceType)
from personal_budget.widgets import ConfirmationModal


class UpdateEntryModal(ModalScreen):
    SUB_TITLE = "Update entry"
    BINDINGS = [("escape", "app.pop_screen", "Cancel")]

    def __init__(
        self, entry: FinancialEntry, modal_title="Update Entry", *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.entry = entry
        self.modal_title = modal_title

    def compose(self) -> ComposeResult:
        yield Label("", classes="modal-title-before")
        yield Label(self.modal_title, classes="modal-title")
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

            yield Label("Start date:")
            yield Input(value=str(self.entry.recurrence.start_date), id="entry_start_date")

            # TODO: only show this if recurrence is MONTHLY
            yield Label("Every X months?")
            yield Input(value=str(self.entry.recurrence.every), id="entry_every")

            yield Label("End Date:")
            end_date_value = (
                str(self.entry.recurrence.end_date)
                if self.entry.recurrence.end_date
                else ""
            )
            yield Input(value=end_date_value, id="end_date")

            yield Button("Save", id="entry_save", variant="primary")
            yield Button("Cancel", id="entry_cancel")

    def _get_values(self):
        def get_date_or_none(value):
            return date.fromisoformat(value) if value else None
        return {
            "description": self.query_one("#entry_description", Input).value,
            "amount": Decimal(self.query_one("#entry_amount", Input).value),
            "category": self.query_one("#entry_category", Input).value,
            "recurrence_type": RecurrenceType[
                str(
                    self.query_one("#entry_recurrence", RadioSet).pressed_button.label
                ).upper()
            ],
            "start_date": date.fromisoformat(self.query_one("#entry_start_date", Input).value),
            "every": int(self.query_one("#entry_every", Input).value),
            "end_date": get_date_or_none(self.query_one("#end_date", Input).value),
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


class ManageEntriesScreen(Screen):
    BINDINGS = [
        ("backspace", "back", "Back"),
        ("escape", "back", "Back"),
        ("insert", "add_entry", "Add Entry"),
        ("delete", "delete_entry", "Delete Entry"),
    ]

    def __init__(
        self, entry_type: EntryType, entries: list[FinancialEntry], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.sub_title: str = (
            "Managing Expenses" if entry_type == EntryType.EXPENSE else "Managing Income"
        )
        self.entry_type = entry_type
        self.entries = entries

    def action_back(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        yield Label(self.sub_title, classes=f"entries-label-{self.entry_type}")
        yield DataTable(id="entries_table", cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one("#entries_table", DataTable)
        table.add_columns("Description", "Amount", "Recurrence", "Category")
        self._sync_table()

    def _sync_table(self) -> None:
        table = self.query_one("#entries_table", DataTable)
        self._sync_table_entries(table, self.entries)

    def _sync_table_entries(
        self, table: DataTable, entries: list[FinancialEntry]
    ) -> None:
        table.clear()

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

    @work
    async def action_add_entry(self) -> None:
        modal_title = (
            "Add Expense" if self.entry_type == EntryType.EXPENSE else "Add Income"
        )
        screen = UpdateEntryModal(FinancialEntry(type=self.entry_type), modal_title)
        result = await self.app.push_screen_wait(screen)
        if result:
            self.entries.append(result)
            self._sync_table()
            if self.entry_type == EntryType.EXPENSE:
                self.notify(f"Added expense {result.description}", title="Expense added")
            else:
                self.notify(f"Added income {result.description}", title="Income added")

    @work
    async def action_delete_entry(self) -> None:
        if not self.entries:
            return

        table = self.query_one("#entries_table", DataTable)
        entry = self.entries[table.cursor_row]
        screen = ConfirmationModal(
            f"Are you sure you want to delete '{entry.description}'?"
        )
        result = await self.app.push_screen_wait(screen)
        if result:
            self.entries.pop(table.cursor_row)
            self._sync_table()
            self.notify("Entry deleted", title="Entry deleted")

    @work
    @on(DataTable.RowSelected, "#entries_table")
    async def on_row_selected(self, event: DataTable.RowSelected) -> None:
        entry = self.entries[event.cursor_row]
        new_entry = await self.app.push_screen_wait(
            UpdateEntryModal(entry, f"Update {self.entry_type} Entry")
        )
        if new_entry:
            self.entries[event.cursor_row] = new_entry
            self._sync_table()
            self.notify(f"Updated entry '{new_entry.description}'", title="Entry updated")


class MainScreen(Screen):
    def __init__(self, state: FinancialState, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state

    BINDINGS = [
        ("e", "manage_expenses", "Manage Expenses"),
        ("i", "manage_income", "Manage Income"),
    ]

    @work
    async def action_manage_expenses(self) -> None:
        screen = ManageEntriesScreen(EntryType.EXPENSE, self.state.expense_entries)
        await self.app.push_screen_wait(screen)
        self._sync_table()

    @work
    async def action_manage_income(self) -> None:
        screen = ManageEntriesScreen(EntryType.INCOME, self.state.income_entries)
        await self.app.push_screen_wait(screen)
        self._sync_table()

    def compose(self) -> ComposeResult:
        # TODO: if state has no entries, invite user to create a new one
        # TODO: if state has entries, display the forecast for the next months,
        #       with option to manage entries
        yield Header()
        yield Label("FORECAST FOR NEXT 12 MONTHS", classes="forecast-title")
        yield DataTable(id="forecast_table", cursor_type="none")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#forecast_table", DataTable)
        table.add_columns("Month", "Expenses", "Income", "Balance")
        self._sync_table()

    def _sync_table(self) -> None:
        table = self.query_one("#forecast_table", DataTable)
        table.clear()
        for month, forecast in self.state.get_forecast_for_next_n_months(12).items():
            balance_style = "red bold" if forecast.balance < Decimal("0") else "blue bold"
            table.add_row(
                month.strftime("%B %Y"),
                Text(f"€{forecast.total_expenses}", style="bold", justify="right"),
                Text(f"€{forecast.total_income}", style="bold", justify="right"),
                Text(f"€{forecast.balance}", style=balance_style, justify="right"),
            )


class BudgetApp(App):
    TITLE = "Personal Budget Planner"
    CSS_PATH = "style.css"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+s", "save_state", "Save"),
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
        yield Label("Loading...")
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen(MainScreen(self.state))

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
