import tempfile
from decimal import Decimal

import pytest

from moomoolah.budget_app import BudgetApp, CurrencySettingsModal
from moomoolah.state import (
    FinancialState,
    format_currency,
    CURRENCY_FORMATS,
)


class TestCurrencyFormatting:
    """Test currency formatting functionality."""

    def test_format_currency_eur(self):
        """Test EUR currency formatting."""
        amount = Decimal("1234.56")
        result = format_currency(amount, "EUR")
        assert result == "€1,234.56"

    def test_format_currency_usd(self):
        """Test USD currency formatting."""
        amount = Decimal("1234.56")
        result = format_currency(amount, "USD")
        assert result == "$1,234.56"

    def test_format_currency_gbp(self):
        """Test GBP currency formatting."""
        amount = Decimal("1234.56")
        result = format_currency(amount, "GBP")
        assert result == "£1,234.56"

    def test_format_currency_jpy(self):
        """Test JPY currency formatting (no decimals)."""
        amount = Decimal("1234.56")
        result = format_currency(amount, "JPY")
        assert result == "¥1,235"  # Rounded to nearest whole number

    def test_format_currency_cad(self):
        """Test CAD currency formatting."""
        amount = Decimal("1234.56")
        result = format_currency(amount, "CAD")
        assert result == "C$1,234.56"

    def test_format_currency_aud(self):
        """Test AUD currency formatting."""
        amount = Decimal("1234.56")
        result = format_currency(amount, "AUD")
        assert result == "A$1,234.56"

    def test_format_currency_brl(self):
        """Test BRL currency formatting (comma decimal, period thousands)."""
        amount = Decimal("1234.56")
        result = format_currency(amount, "BRL")
        assert result == "R$1.234,56"

    def test_format_currency_tl(self):
        """Test TL currency formatting."""
        amount = Decimal("1234.56")
        result = format_currency(amount, "TL")
        assert result == "₺1.234,56"

    def test_format_currency_small_amount(self):
        """Test formatting small amounts."""
        amount = Decimal("10.50")
        result = format_currency(amount, "USD")
        assert result == "$10.50"

    def test_format_currency_large_amount(self):
        """Test formatting large amounts with thousands separators."""
        amount = Decimal("1234567.89")
        result = format_currency(amount, "EUR")
        assert result == "€1,234,567.89"

    def test_format_currency_zero_amount(self):
        """Test formatting zero amounts."""
        amount = Decimal("0.00")
        result = format_currency(amount, "USD")
        assert result == "$0.00"

    def test_format_currency_negative_amount(self):
        """Test formatting negative amounts."""
        amount = Decimal("-100.50")
        result = format_currency(amount, "EUR")
        assert result == "€-100.50"

    def test_currency_formats_completeness(self):
        """Test that all expected currencies are defined in CURRENCY_FORMATS."""
        expected_currencies = {"EUR", "USD", "GBP", "JPY", "CAD", "AUD", "BRL", "TL"}
        actual_currencies = set(CURRENCY_FORMATS.keys())
        assert actual_currencies == expected_currencies

    def test_currency_formats_structure(self):
        """Test that all currency formats have the expected structure."""
        for currency_code, currency_format in CURRENCY_FORMATS.items():
            assert hasattr(currency_format, "symbol")
            assert hasattr(currency_format, "code")
            assert hasattr(currency_format, "decimal_places")
            assert hasattr(currency_format, "decimal_separator")
            assert hasattr(currency_format, "thousands_separator")
            assert currency_format.code == currency_code


class TestFinancialStateCurrency:
    """Test currency configuration in FinancialState."""

    def test_default_currency_code(self):
        """Test that default currency is EUR."""
        state = FinancialState()
        assert state.currency_code == "EUR"

    def test_currency_code_persistence(self):
        """Test that currency code is persisted to JSON."""
        state = FinancialState()
        state.currency_code = "USD"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state.to_json_file(f.name)

            # Load state from file
            loaded_state = FinancialState.from_json_file(f.name)
            assert loaded_state.currency_code == "USD"

    def test_currency_code_backward_compatibility(self):
        """Test that old state files without currency_code still work."""
        # Create a state file without currency_code (simulating old format)
        state_json = '{"all_entries": {"INCOME": [], "EXPENSE": []}}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(state_json)
            f.flush()

            # Load state from file - should default to EUR
            loaded_state = FinancialState.from_json_file(f.name)
            assert loaded_state.currency_code == "EUR"


class TestCurrencySettingsModal:
    """Test the currency settings modal."""

    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.to_json_file(f.name)
            yield f.name

    async def test_currency_settings_modal_creation(self, temp_state_file):
        """Test that the currency settings modal can be created."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Create modal
            modal = CurrencySettingsModal("EUR")
            assert modal.current_currency == "EUR"

    async def test_currency_change_via_keyboard(self, temp_state_file):
        """Test changing currency via keyboard shortcut."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Initial currency should be EUR
            assert app.state.currency_code == "EUR"

            # Press 'c' to open currency settings
            await pilot.press("c")
            await pilot.pause()

            # Check that currency settings modal is open
            assert len(app.screen_stack) > 1  # Modal should be pushed

    async def test_currency_change_updates_display(self, temp_state_file):
        """Test that changing currency updates all display locations."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Change currency to USD
            app.state.currency_code = "USD"
            app.screen._sync_table()  # Trigger table refresh

            # Check that forecast table shows USD symbols
            forecast_table = app.screen.query_one("#forecast_table")
            first_row_cells = list(forecast_table.get_row_at(0))

            # Check that balance column contains $ symbol
            balance_text = first_row_cells[3].plain
            assert "$" in balance_text
            assert "€" not in balance_text


class TestCurrencyIntegration:
    """Test currency integration with the full application."""

    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state = FinancialState()
            state.to_json_file(f.name)
            yield f.name

    async def test_currency_persists_across_app_restart(self, temp_state_file):
        """Test that currency setting persists when app is restarted."""
        # First app instance - change currency
        app1 = BudgetApp(state_file=temp_state_file)
        async with app1.run_test() as pilot:
            await pilot.pause()
            app1.state.currency_code = "GBP"
            app1.action_save_state()

        # Second app instance - should load the saved currency
        app2 = BudgetApp(state_file=temp_state_file)
        async with app2.run_test() as pilot:
            await pilot.pause()
            assert app2.state.currency_code == "GBP"

    async def test_currency_affects_all_views(self, temp_state_file):
        """Test that currency change affects all application views."""
        app = BudgetApp(state_file=temp_state_file)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Change to BRL which has different formatting
            app.state.currency_code = "BRL"
            app.screen._sync_table()

            # Check main screen forecast table
            forecast_table = app.screen.query_one("#forecast_table")
            first_row_cells = list(forecast_table.get_row_at(0))
            balance_text = first_row_cells[3].plain
            assert "R$" in balance_text

            # Check history table
            history_table = app.screen.query_one("#history_table")
            if history_table.row_count > 0:
                history_row_cells = list(history_table.get_row_at(0))
                history_balance_text = history_row_cells[3].plain
                assert "R$" in history_balance_text
