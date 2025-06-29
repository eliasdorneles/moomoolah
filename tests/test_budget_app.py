import tempfile
from datetime import date
from decimal import Decimal

import pytest
from textual.widgets import DataTable

from moomoolah.budget_app import BudgetApp, MainScreen
from moomoolah.state import (
    EntryType,
    FinancialEntry,
    FinancialState,
    Recurrence,
    RecurrenceType,
)


@pytest.fixture
def basic_temp_state_file():
    """Create a basic temporary state file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # Create a basic state with some test data
        state = FinancialState()
        state.add_entry(
            FinancialEntry(
                amount=Decimal("1000"),
                description="Test Income",
                type=EntryType.INCOME,
                category="Income",
                recurrence=Recurrence(
                    type=RecurrenceType.MONTHLY,
                    start_date=date(2024, 1, 1),
                ),
            )
        )
        state.to_json_file(f.name)
        yield f.name


class TestBudgetApp:
    """Test the main BudgetApp functionality."""

    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Create a basic state with some test data
            state = FinancialState()
            state.add_entry(
                FinancialEntry(
                    amount=Decimal("2000"),
                    description="Test Salary",
                    type=EntryType.INCOME,
                    category="Income",
                    recurrence=Recurrence(
                        type=RecurrenceType.MONTHLY,
                        start_date=date(2024, 1, 1),
                    ),
                )
            )
            state.add_entry(
                FinancialEntry(
                    amount=Decimal("800"),
                    description="Test Rent",
                    type=EntryType.EXPENSE,
                    category="Housing",
                    recurrence=Recurrence(
                        type=RecurrenceType.MONTHLY,
                        start_date=date(2024, 1, 1),
                    ),
                )
            )
            state.to_json_file(f.name)
            yield f.name

    async def test_app_initialization(self, temp_state_file):
        """Test that the app initializes correctly with a state file."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()  # Wait for the app to fully initialize
            # Check that the main screen is loaded
            assert isinstance(app.screen, MainScreen)
            # Check that forecast table is present
            forecast_table = app.screen.query_one("#forecast_table", DataTable)
            assert forecast_table is not None

    async def test_forecast_table_displays_data(self, temp_state_file):
        """Test that the forecast table displays financial data correctly."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            forecast_table = app.screen.query_one("#forecast_table", DataTable)

            # Should have at least one row of data
            assert forecast_table.row_count > 0

            # Check that columns are set up correctly
            assert len(forecast_table.columns) == 4
            column_labels = [col.label.plain for col in forecast_table.columns.values()]
            assert column_labels == ["Month", "Expenses", "Income", "Balance"]

    async def test_navigation_to_manage_expenses(self, temp_state_file):
        """Test navigation to expense management screen using keyboard shortcut."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test() as pilot:
            # Press 'e' key to navigate to expenses
            await pilot.press("e")
            await pilot.pause()

            # Should be on ManageEntriesScreen now
            assert app.screen.__class__.__name__ == "ManageEntriesScreen"
            assert app.screen.sub_title == "Managing Expenses"

    async def test_navigation_to_manage_income(self, temp_state_file):
        """Test navigation to income management screen using keyboard shortcut."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test() as pilot:
            # Press 'i' key to navigate to income
            await pilot.press("i")
            await pilot.pause()

            # Should be on ManageEntriesScreen now
            assert app.screen.__class__.__name__ == "ManageEntriesScreen"
            assert app.screen.sub_title == "Managing Income"

    async def test_save_state_action(self, temp_state_file):
        """Test that Ctrl+S saves the state."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test() as pilot:
            # Trigger save action
            await pilot.press("ctrl+s")
            await pilot.pause()

            # Check that notification was displayed (implicit test via no exception)
            # The actual file saving is tested in state tests

    async def test_forecast_updates_after_adding_expense(self, temp_state_file):
        """Test that the main screen forecast updates after adding an expense."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()

            # Get initial forecast data
            forecast_table = app.screen.query_one("#forecast_table", DataTable)

            # Get first month's balance from the forecast table
            first_row_cells = list(forecast_table.get_row_at(0))
            initial_balance_text = first_row_cells[3].plain  # Balance column
            initial_balance = Decimal(initial_balance_text.replace("€", ""))

            # Navigate to expense management
            await pilot.press("e")
            await pilot.pause()

            # Add a new expense
            await pilot.press("insert")  # Trigger add entry action
            await pilot.pause()

            # Fill in the expense form
            description_input = app.screen.query_one("#entry_description")
            await pilot.click("#entry_description")
            description_input.value = "Test Expense"

            amount_input = app.screen.query_one("#entry_amount")
            await pilot.click("#entry_amount")
            amount_input.value = "300"

            category_input = app.screen.query_one("#entry_category")
            await pilot.click("#entry_category")
            category_input.value = "Test Category"

            # Set start date (required field)
            start_date_input = app.screen.query_one("#entry_start_date")
            await pilot.click("#entry_start_date")
            start_date_input.value = "2024-01-01"

            # Set every field (required)
            every_input = app.screen.query_one("#entry_every")
            await pilot.click("#entry_every")
            every_input.value = "1"

            # Save the entry
            await pilot.click("#entry_save")
            await pilot.pause()

            # Check that we're back on ManageEntriesScreen after saving
            assert app.screen.__class__.__name__ == "ManageEntriesScreen"

            # Navigate back to main screen
            await pilot.press("escape")
            await pilot.pause()

            # Verify we're back on main screen
            assert isinstance(app.screen, MainScreen)

            # Check that the forecast table has been updated
            updated_forecast_table = app.screen.query_one("#forecast_table", DataTable)

            # Get the updated balance for the first month
            updated_first_row_cells = list(updated_forecast_table.get_row_at(0))
            updated_balance_text = updated_first_row_cells[3].plain  # Balance column
            updated_balance = Decimal(updated_balance_text.replace("€", ""))

            # The balance should have decreased by 300 (the expense amount)
            expected_balance = initial_balance - Decimal("300")
            assert updated_balance == expected_balance, (
                f"Expected balance {expected_balance}, got {updated_balance}"
            )

    async def test_add_entry_from_main_screen_expense(self, temp_state_file):
        """Test adding an expense directly from main screen using Insert key."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()

            # Get initial forecast data
            forecast_table = app.screen.query_one("#forecast_table", DataTable)
            first_row_cells = list(forecast_table.get_row_at(0))
            initial_balance_text = first_row_cells[3].plain  # Balance column
            initial_balance = Decimal(initial_balance_text.replace("€", ""))

            # Press Insert to add entry from main screen
            await pilot.press("insert")
            await pilot.pause()

            # Should see entry type modal - click Expense
            await pilot.click("#add_expense")
            await pilot.pause()

            # Should now see the entry form - fill it out
            description_input = app.screen.query_one("#entry_description")
            await pilot.click("#entry_description")
            description_input.value = "Direct Expense"

            amount_input = app.screen.query_one("#entry_amount")
            await pilot.click("#entry_amount")
            amount_input.value = "150"

            category_input = app.screen.query_one("#entry_category")
            await pilot.click("#entry_category")
            category_input.value = "Test"

            # Set required fields
            start_date_input = app.screen.query_one("#entry_start_date")
            await pilot.click("#entry_start_date")
            start_date_input.value = "2024-01-01"

            every_input = app.screen.query_one("#entry_every")
            await pilot.click("#entry_every")
            every_input.value = "1"

            # Save the entry
            await pilot.click("#entry_save")
            await pilot.pause()

            # Should be back on main screen
            assert isinstance(app.screen, MainScreen)

            # Check that the forecast updated
            updated_forecast_table = app.screen.query_one("#forecast_table", DataTable)
            updated_first_row_cells = list(updated_forecast_table.get_row_at(0))
            updated_balance_text = updated_first_row_cells[3].plain
            updated_balance = Decimal(updated_balance_text.replace("€", ""))

            # Balance should have decreased by 150
            expected_balance = initial_balance - Decimal("150")
            assert updated_balance == expected_balance, (
                f"Expected balance {expected_balance}, got {updated_balance}"
            )

    async def test_add_entry_from_main_screen_income(self, temp_state_file):
        """Test adding income directly from main screen using Insert key."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()

            # Get initial forecast data
            forecast_table = app.screen.query_one("#forecast_table", DataTable)
            first_row_cells = list(forecast_table.get_row_at(0))
            initial_balance_text = first_row_cells[3].plain
            initial_balance = Decimal(initial_balance_text.replace("€", ""))

            # Press Insert to add entry from main screen
            await pilot.press("insert")
            await pilot.pause()

            # Should see entry type modal - click Income
            await pilot.click("#add_income")
            await pilot.pause()

            # Fill out the income form
            description_input = app.screen.query_one("#entry_description")
            await pilot.click("#entry_description")
            description_input.value = "Bonus"

            amount_input = app.screen.query_one("#entry_amount")
            await pilot.click("#entry_amount")
            amount_input.value = "500"

            category_input = app.screen.query_one("#entry_category")
            await pilot.click("#entry_category")
            category_input.value = "Extra"

            # Set required fields
            start_date_input = app.screen.query_one("#entry_start_date")
            await pilot.click("#entry_start_date")
            start_date_input.value = "2024-01-01"

            every_input = app.screen.query_one("#entry_every")
            await pilot.click("#entry_every")
            every_input.value = "1"

            # Save the entry
            await pilot.click("#entry_save")
            await pilot.pause()

            # Should be back on main screen
            assert isinstance(app.screen, MainScreen)

            # Check that the forecast updated
            updated_forecast_table = app.screen.query_one("#forecast_table", DataTable)
            updated_first_row_cells = list(updated_forecast_table.get_row_at(0))
            updated_balance_text = updated_first_row_cells[3].plain
            updated_balance = Decimal(updated_balance_text.replace("€", ""))

            # Balance should have increased by 500
            expected_balance = initial_balance + Decimal("500")
            assert updated_balance == expected_balance, (
                f"Expected balance {expected_balance}, got {updated_balance}"
            )

    async def test_add_entry_from_main_screen_cancel(self, temp_state_file):
        """Test canceling the add entry flow from main screen."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()

            # Get initial forecast data
            forecast_table = app.screen.query_one("#forecast_table", DataTable)
            first_row_cells = list(forecast_table.get_row_at(0))
            initial_balance_text = first_row_cells[3].plain
            initial_balance = Decimal(initial_balance_text.replace("€", ""))

            # Press Insert to add entry from main screen
            await pilot.press("insert")
            await pilot.pause()

            # Cancel the entry type modal
            await pilot.press("escape")
            await pilot.pause()

            # Should be back on main screen with no changes
            assert isinstance(app.screen, MainScreen)

            # Check that forecast is unchanged
            updated_forecast_table = app.screen.query_one("#forecast_table", DataTable)
            updated_first_row_cells = list(updated_forecast_table.get_row_at(0))
            updated_balance_text = updated_first_row_cells[3].plain
            updated_balance = Decimal(updated_balance_text.replace("€", ""))

            # Balance should be unchanged
            assert updated_balance == initial_balance

    async def test_enter_on_empty_expense_list(self):
        """Test that pressing Enter on empty expense list doesn't crash."""
        # Create a completely empty state file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            empty_state = FinancialState()
            empty_state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test() as pilot:
                await pilot.pause()

                # Navigate to expense management (truly empty)
                await pilot.press("e")
                await pilot.pause()

                # Press Enter on empty list - this should not crash
                await pilot.press("enter")
                await pilot.pause()

                # Should still be on the manage entries screen
                assert app.screen.__class__.__name__ == "ManageEntriesScreen"

    async def test_enter_on_empty_income_list(self):
        """Test that pressing Enter on truly empty income list doesn't crash."""
        # Create a completely empty state file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            empty_state = FinancialState()
            empty_state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test() as pilot:
                await pilot.pause()

                # Navigate to income management (truly empty)
                await pilot.press("i")
                await pilot.pause()

                # Press Enter on empty list - this should not crash
                await pilot.press("enter")
                await pilot.pause()

                # Should still be on the manage entries screen
                assert app.screen.__class__.__name__ == "ManageEntriesScreen"


class TestManageEntriesScreen:
    """Test the ManageEntriesScreen functionality."""

    @pytest.fixture
    def sample_entries(self):
        """Create sample financial entries for testing."""
        return [
            FinancialEntry(
                amount=Decimal("1000"),
                description="Salary",
                type=EntryType.INCOME,
                category="Job",
                recurrence=Recurrence(
                    type=RecurrenceType.MONTHLY,
                    start_date=date(2024, 1, 1),
                ),
            ),
            FinancialEntry(
                amount=Decimal("500"),
                description="Rent",
                type=EntryType.EXPENSE,
                category="Housing",
                recurrence=Recurrence(
                    type=RecurrenceType.MONTHLY,
                    start_date=date(2024, 1, 1),
                ),
            ),
        ]

    async def test_entries_table_displays_data(
        self, sample_entries, basic_temp_state_file
    ):
        """Test that entries are displayed correctly in the table."""
        from moomoolah.budget_app import ManageEntriesScreen

        app = BudgetApp(state_file=basic_temp_state_file)
        expenses = [e for e in sample_entries if e.type == EntryType.EXPENSE]

        async with app.run_test() as pilot:
            await pilot.pause()
            screen = ManageEntriesScreen(EntryType.EXPENSE, expenses)
            app.push_screen(screen)
            await pilot.pause()

            entries_table = app.screen.query_one("#entries_table", DataTable)
            assert entries_table.row_count == 1  # One expense entry

            # Check table columns
            column_labels = [col.label.plain for col in entries_table.columns.values()]
            assert column_labels == ["Description", "Amount", "Recurrence", "Category"]

    async def test_back_navigation_with_escape(
        self, sample_entries, basic_temp_state_file
    ):
        """Test that escape key navigates back from entries screen."""
        from moomoolah.budget_app import ManageEntriesScreen

        app = BudgetApp(state_file=basic_temp_state_file)
        expenses = [e for e in sample_entries if e.type == EntryType.EXPENSE]

        async with app.run_test() as pilot:
            await pilot.pause()  # Wait for main screen
            screen = ManageEntriesScreen(EntryType.EXPENSE, expenses)
            app.push_screen(screen)
            await pilot.pause()

            # Press escape to go back
            await pilot.press("escape")
            await pilot.pause()

            # Should be back to main screen
            assert isinstance(app.screen, MainScreen)

    async def test_back_navigation_with_backspace(
        self, sample_entries, basic_temp_state_file
    ):
        """Test that backspace key navigates back from entries screen."""
        from moomoolah.budget_app import ManageEntriesScreen

        app = BudgetApp(state_file=basic_temp_state_file)
        expenses = [e for e in sample_entries if e.type == EntryType.EXPENSE]

        async with app.run_test() as pilot:
            await pilot.pause()  # Wait for main screen
            screen = ManageEntriesScreen(EntryType.EXPENSE, expenses)
            app.push_screen(screen)
            await pilot.pause()

            # Press backspace to go back
            await pilot.press("backspace")
            await pilot.pause()

            # Should be back to main screen
            assert isinstance(app.screen, MainScreen)


class TestConfirmationModal:
    """Test the ConfirmationModal widget."""

    async def test_confirmation_modal_yes_button(self, basic_temp_state_file):
        """Test that clicking 'Yes' returns True."""
        from moomoolah.widgets import ConfirmationModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            modal = ConfirmationModal("Are you sure?")

            # Start the modal and get the future
            app.push_screen(modal)
            await pilot.pause()

            # Click Yes button
            await pilot.click("#confirmation_yes")
            await pilot.pause()

            # Modal should be dismissed, check that we're back to main screen
            assert isinstance(app.screen, MainScreen)

    async def test_confirmation_modal_no_button(self, basic_temp_state_file):
        """Test that clicking 'No' returns False."""
        from moomoolah.widgets import ConfirmationModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            modal = ConfirmationModal("Are you sure?")

            # Start the modal
            app.push_screen(modal)
            await pilot.pause()

            # Click No button
            await pilot.click("#confirmation_no")
            await pilot.pause()

            # Modal should be dismissed, check that we're back to main screen
            assert isinstance(app.screen, MainScreen)

    async def test_confirmation_modal_escape_key(self, basic_temp_state_file):
        """Test that escape key cancels the modal."""
        from moomoolah.widgets import ConfirmationModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            modal = ConfirmationModal("Are you sure?")

            # Start the modal
            app.push_screen(modal)
            await pilot.pause()

            # Press escape to cancel
            await pilot.press("escape")
            await pilot.pause()

            # Modal should be dismissed, check that we're back to main screen
            assert isinstance(app.screen, MainScreen)

    async def test_confirmation_modal_arrow_keys(self, basic_temp_state_file):
        """Test that left/right arrow keys change focus between buttons."""
        from moomoolah.widgets import ConfirmationModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            modal = ConfirmationModal("Are you sure?")

            # Start the modal
            app.push_screen(modal)
            await pilot.pause()

            # Test that arrow keys navigate between buttons
            await pilot.press("right")
            await pilot.pause()

            await pilot.press("left")
            await pilot.pause()

            # Press Enter on focused button (should be Yes button after left arrow)
            await pilot.press("enter")
            await pilot.pause()

            # Modal should be dismissed, back to main screen
            assert isinstance(app.screen, MainScreen)


class TestUpdateEntryModal:
    """Test the UpdateEntryModal functionality."""

    @pytest.fixture
    def sample_entry(self):
        """Create a sample entry for testing."""
        return FinancialEntry(
            amount=Decimal("100"),
            description="Test Entry",
            type=EntryType.EXPENSE,
            category="Test",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2024, 1, 1),
            ),
        )

    async def test_update_entry_modal_cancel(self, sample_entry, basic_temp_state_file):
        """Test that cancel button dismisses modal."""
        from moomoolah.budget_app import UpdateEntryModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test(size=(120, 40)) as pilot:  # Larger screen for modal
            await pilot.pause()
            modal = UpdateEntryModal(sample_entry)

            # Start the modal
            app.push_screen(modal)
            await pilot.pause()

            # Click Cancel button
            await pilot.click("#entry_cancel")
            await pilot.pause()

            # Modal should be dismissed, back to main screen
            assert isinstance(app.screen, MainScreen)

    async def test_update_entry_modal_form_fields_populated(
        self, sample_entry, basic_temp_state_file
    ):
        """Test that form fields are populated with entry data."""
        from moomoolah.budget_app import UpdateEntryModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test(size=(120, 40)) as pilot:  # Larger screen for modal
            await pilot.pause()
            modal = UpdateEntryModal(sample_entry)
            app.push_screen(modal)
            await pilot.pause()

            # Check that fields are populated correctly
            description_input = app.screen.query_one("#entry_description")
            assert description_input.value == "Test Entry"

            amount_input = app.screen.query_one("#entry_amount")
            assert amount_input.value == "100"

            category_input = app.screen.query_one("#entry_category")
            assert category_input.value == "Test"

    async def test_when_user_press_enter_in_update_entry_modal_then_save_entry(
        self, sample_entry, basic_temp_state_file
    ):
        from moomoolah.budget_app import UpdateEntryModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            modal = UpdateEntryModal(sample_entry, "Test Modal")

            # Push the modal to the screen
            app.push_screen(modal)
            await pilot.pause()

            # Modify a field to test the save
            description_input = app.screen.query_one("#entry_description")
            description_input.value = "Updated Test Entry"

            # Press ENTER to save - this should trigger the save action
            await pilot.press("enter")
            await pilot.pause()

            # Modal should be dismissed, back to main screen
            assert isinstance(app.screen, MainScreen)


class TestUnsavedChanges:
    """Test the unsaved changes tracking functionality."""

    async def test_app_starts_with_no_unsaved_changes(self):
        """Test that app starts with no unsaved changes indicator."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test() as pilot:
                await pilot.pause()

                # App should start with no unsaved changes
                assert not app.has_unsaved_changes
                assert app.title == "MooMoolah - Personal Budget Planner"

    async def test_title_shows_asterisk_when_unsaved_changes(self):
        """Test that title shows asterisk when there are unsaved changes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test() as pilot:
                await pilot.pause()

                # Mark changes as unsaved
                app.mark_unsaved_changes()

                # Title should show asterisk
                assert app.has_unsaved_changes
                assert app.title == "MooMoolah - Personal Budget Planner *"

    async def test_save_removes_unsaved_changes_indicator(self):
        """Test that saving removes the unsaved changes indicator."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test() as pilot:
                await pilot.pause()

                # Mark changes as unsaved
                app.mark_unsaved_changes()
                assert app.has_unsaved_changes
                assert app.title == "MooMoolah - Personal Budget Planner *"

                # Save the state
                await pilot.press("ctrl+s")
                await pilot.pause()

                # Unsaved changes should be cleared
                assert not app.has_unsaved_changes
                assert app.title == "MooMoolah - Personal Budget Planner"

    async def test_adding_entry_marks_unsaved_changes(self):
        """Test that adding an entry marks the app as having unsaved changes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test(size=(120, 50)) as pilot:
                await pilot.pause()

                # Initially no unsaved changes
                assert not app.has_unsaved_changes
                assert app.title == "MooMoolah - Personal Budget Planner"

                # Add entry from main screen
                await pilot.press("insert")
                await pilot.pause()

                # Choose expense
                await pilot.click("#add_expense")
                await pilot.pause()

                # Fill out form
                description_input = app.screen.query_one("#entry_description")
                await pilot.click("#entry_description")
                description_input.value = "Test Expense"

                amount_input = app.screen.query_one("#entry_amount")
                await pilot.click("#entry_amount")
                amount_input.value = "100"

                category_input = app.screen.query_one("#entry_category")
                await pilot.click("#entry_category")
                category_input.value = "Test"

                start_date_input = app.screen.query_one("#entry_start_date")
                await pilot.click("#entry_start_date")
                start_date_input.value = "2024-01-01"

                every_input = app.screen.query_one("#entry_every")
                await pilot.click("#entry_every")
                every_input.value = "1"

                # Save the entry
                await pilot.click("#entry_save")
                await pilot.pause()

                # Should now have unsaved changes
                assert app.has_unsaved_changes
                assert app.title == "MooMoolah - Personal Budget Planner *"

    async def test_modifying_entry_marks_unsaved_changes(self):
        """Test that modifying an entry marks the app as having unsaved changes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.add_entry(
                FinancialEntry(
                    amount=Decimal("100"),
                    description="Original Entry",
                    type=EntryType.EXPENSE,
                    category="Test",
                    recurrence=Recurrence(
                        type=RecurrenceType.MONTHLY,
                        start_date=date(2024, 1, 1),
                    ),
                )
            )
            state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test(size=(120, 50)) as pilot:
                await pilot.pause()

                # Initially no unsaved changes
                assert not app.has_unsaved_changes

                # Navigate to expense management
                await pilot.press("e")
                await pilot.pause()

                # Click on the entry to edit it
                await pilot.click("#entries_table")
                await pilot.press("enter")
                await pilot.pause()

                # Modify the description
                description_input = app.screen.query_one("#entry_description")
                await pilot.click("#entry_description")
                description_input.value = "Modified Entry"

                # Save the changes
                await pilot.click("#entry_save")
                await pilot.pause()

                # Should now have unsaved changes
                assert app.has_unsaved_changes
                assert app.title == "MooMoolah - Personal Budget Planner *"

    async def test_deleting_entry_marks_unsaved_changes(self):
        """Test that deleting an entry marks the app as having unsaved changes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.add_entry(
                FinancialEntry(
                    amount=Decimal("100"),
                    description="Entry to Delete",
                    type=EntryType.EXPENSE,
                    category="Test",
                    recurrence=Recurrence(
                        type=RecurrenceType.MONTHLY,
                        start_date=date(2024, 1, 1),
                    ),
                )
            )
            state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test(size=(120, 50)) as pilot:
                await pilot.pause()

                # Initially no unsaved changes
                assert not app.has_unsaved_changes

                # Navigate to expense management
                await pilot.press("e")
                await pilot.pause()

                # Delete the entry
                await pilot.press("delete")
                await pilot.pause()

                # Confirm deletion
                await pilot.click("#confirmation_yes")
                await pilot.pause()

                # Should now have unsaved changes
                assert app.has_unsaved_changes
                assert app.title == "MooMoolah - Personal Budget Planner *"

    async def test_quit_with_no_unsaved_changes_quits_immediately(self):
        """Test that quitting with no unsaved changes quits immediately."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test() as pilot:
                await pilot.pause()

                # No unsaved changes initially
                assert not app.has_unsaved_changes

                # Quit should work without confirmation
                await pilot.press("ctrl+q")
                await pilot.pause()

                # App should have exited (this test passes if no exception occurs)

    async def test_quit_with_unsaved_changes_shows_confirmation(self):
        """Test that quitting with unsaved changes shows confirmation dialog."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test(size=(120, 50)) as pilot:
                await pilot.pause()

                # Mark unsaved changes
                app.mark_unsaved_changes()
                assert app.has_unsaved_changes

                # Try to quit
                await pilot.press("ctrl+q")
                await pilot.pause()

                # Should show confirmation modal
                # Check that we can see the confirmation buttons
                yes_button = app.screen.query_one("#confirmation_yes")
                no_button = app.screen.query_one("#confirmation_no")
                assert yes_button is not None
                assert no_button is not None

    async def test_quit_confirmation_no_cancels_quit(self):
        """Test that clicking 'No' in quit confirmation cancels the quit."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.to_json_file(f.name)

            app = BudgetApp(state_file=f.name)
            async with app.run_test(size=(120, 50)) as pilot:
                await pilot.pause()

                # Mark unsaved changes
                app.mark_unsaved_changes()

                # Try to quit
                await pilot.press("ctrl+q")
                await pilot.pause()

                # Click No to cancel quit
                await pilot.click("#confirmation_no")
                await pilot.pause()

                # Should be back on main screen
                assert isinstance(app.screen, MainScreen)
                # Unsaved changes should still be marked
                assert app.has_unsaved_changes


class TestEntryTypeModal:
    """Test the EntryTypeModal widget."""

    async def test_entry_type_modal_expense_button(self, basic_temp_state_file):
        """Test that clicking 'Expense' returns EntryType.EXPENSE."""
        from moomoolah.budget_app import EntryTypeModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            modal = EntryTypeModal()

            # Start the modal
            app.push_screen(modal)
            await pilot.pause()

            # Click Expense button
            await pilot.click("#add_expense")
            await pilot.pause()

            # Modal should be dismissed, check that we're back to main screen
            assert isinstance(app.screen, MainScreen)

    async def test_entry_type_modal_income_button(self, basic_temp_state_file):
        """Test that clicking 'Income' returns EntryType.INCOME."""
        from moomoolah.budget_app import EntryTypeModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            modal = EntryTypeModal()

            # Start the modal
            app.push_screen(modal)
            await pilot.pause()

            # Click Income button
            await pilot.click("#add_income")
            await pilot.pause()

            # Modal should be dismissed, check that we're back to main screen
            assert isinstance(app.screen, MainScreen)

    async def test_entry_type_modal_escape_key(self, basic_temp_state_file):
        """Test that escape key cancels the modal."""
        from moomoolah.budget_app import EntryTypeModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            modal = EntryTypeModal()

            # Start the modal
            app.push_screen(modal)
            await pilot.pause()

            # Press escape to cancel
            await pilot.press("escape")
            await pilot.pause()

            # Modal should be dismissed, check that we're back to main screen
            assert isinstance(app.screen, MainScreen)

    async def test_entry_type_modal_arrow_keys(self, basic_temp_state_file):
        """Test that left/right arrow keys change focus between buttons."""
        from moomoolah.budget_app import EntryTypeModal

        app = BudgetApp(state_file=basic_temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            modal = EntryTypeModal()

            # Start the modal
            app.push_screen(modal)
            await pilot.pause()

            # Test that arrow keys navigate between buttons
            await pilot.press("right")
            await pilot.pause()

            await pilot.press("left")
            await pilot.pause()

            # Press Enter on focused button (should be Expense button after left arrow)
            await pilot.press("enter")
            await pilot.pause()

            # Modal should be dismissed, back to main screen
            assert isinstance(app.screen, MainScreen)


class TestDoubleEnterBugFix:
    """Test for the double ENTER key trigger bug fix."""

    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState(
                expenses=[],
                incomes=[],
            )
            f.write(state.model_dump_json())
            f.flush()
            yield f.name

    async def test_modify_entry_enter_key_no_double_trigger(self, temp_state_file):
        """Test that pressing ENTER in modify entry dialog doesn't double-trigger save."""
        from moomoolah.budget_app import UpdateEntryModal
        from moomoolah.state import (
            FinancialEntry,
            EntryType,
            Recurrence,
            RecurrenceType,
        )
        from datetime import date

        app = BudgetApp(state_file=temp_state_file)

        # Create a sample entry to modify
        entry = FinancialEntry(
            description="Test Entry",
            amount=100,
            category="Test",
            type=EntryType.EXPENSE,
            recurrence=Recurrence(
                type=RecurrenceType.ONE_TIME, start_date=date(2024, 1, 1), every=1
            ),
        )

        # Create the modal directly
        modal = UpdateEntryModal(entry, "Test Modal")

        async with app.run_test(size=(120, 50)) as pilot:
            # Push the modal onto the screen
            app.push_screen(modal)
            await pilot.pause()

            # Mock the dismiss method to count how many times it's called
            original_dismiss = modal.dismiss
            dismiss_count = 0

            def mock_dismiss(result=None):
                nonlocal dismiss_count
                dismiss_count += 1
                return original_dismiss(result)

            modal.dismiss = mock_dismiss

            # Press ENTER - this should only trigger save once
            await pilot.press("enter")
            await pilot.pause()

            # Check that dismiss was called exactly once (not double-triggered)
            assert dismiss_count == 1, (
                f"Expected dismiss to be called once, but was called {dismiss_count} times"
            )
