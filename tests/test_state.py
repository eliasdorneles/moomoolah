import os
import tempfile
from datetime import date
from decimal import Decimal

from moomoolah.state import (
    EntryType,
    FinancialEntry,
    FinancialState,
    Recurrence,
    RecurrenceType,
)


def test_financial_state__get_forecast_balance__simple_income():
    state = FinancialState()
    state.add_entry(
        FinancialEntry(
            amount=Decimal("1000"),
            description="Salary",
            type=EntryType.INCOME,
            category="Income",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2022, 1, 1),
            ),
        )
    )
    # when:
    forecast = state.get_monthly_forecast(date(2024, 1, 1))
    # then:
    assert forecast.total_income == Decimal("1000")
    assert forecast.total_expenses == Decimal("0")
    assert forecast.balance == Decimal("1000")


def test_financial_state__get_forecast_balance__simple_income_and_expense():
    state = FinancialState()
    state.add_entry(
        FinancialEntry(
            amount=Decimal("1000"),
            description="Salary",
            type=EntryType.INCOME,
            category="Income",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2022, 1, 1),
            ),
        )
    )
    state.add_entry(
        FinancialEntry(
            amount=Decimal("500"),
            description="Rent",
            type=EntryType.EXPENSE,
            category="Essentials",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2021, 1, 5),
            ),
        )
    )
    # when:
    forecast = state.get_monthly_forecast(date(2024, 1, 1))
    # then:
    assert forecast.total_income == Decimal("1000")
    assert forecast.total_expenses == Decimal("500")
    assert forecast.balance == Decimal("500")
    # when:
    forecast = state.get_monthly_forecast(date(2024, 2, 10))
    # then:
    assert forecast.total_income == Decimal("1000")
    assert forecast.total_expenses == Decimal("500")
    assert forecast.balance == Decimal("500")


def test_financial_state__get_forecast_balance__income_and_complex_expense():
    # given:
    state = FinancialState()
    state.add_entry(
        FinancialEntry(
            amount=Decimal("1000"),
            description="Salary",
            type=EntryType.INCOME,
            category="Income",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2022, 1, 1),
            ),
        )
    )
    # expenses
    state.add_entry(
        FinancialEntry(
            amount=Decimal("500"),
            description="Rent",
            type=EntryType.EXPENSE,
            category="Essentials",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2024, 1, 5),
            ),
        )
    )
    state.add_entry(
        FinancialEntry(
            amount=Decimal("100"),
            description="Groceries",
            type=EntryType.EXPENSE,
            category="Essentials",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2024, 1, 15),
            ),
        )
    )
    state.add_entry(
        FinancialEntry(
            amount=Decimal("80"),
            description="Internet",
            type=EntryType.EXPENSE,
            category="Essentials",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2024, 2, 5),
                every=3,  # every 3 months, starting from February
            ),
        )
    )
    # when:
    forecast1 = state.get_monthly_forecast(date(2024, 1, 1))
    # then:
    assert forecast1.total_income == Decimal("1000")
    assert forecast1.total_expenses == Decimal("600")
    assert forecast1.balance == Decimal("400")
    # and when:
    forecast2 = state.get_monthly_forecast(date(2024, 2, 10))
    # then:
    assert forecast2.total_income == Decimal("1000")
    assert forecast2.total_expenses == Decimal("680")
    assert forecast2.balance == Decimal("320")
    # and when:
    forecast3 = state.get_monthly_forecast(date(2024, 3, 10))
    # then:
    assert forecast3.total_income == forecast1.total_income
    assert forecast3.total_expenses == forecast1.total_expenses
    assert forecast3.balance == forecast1.balance
    # and when:
    forecast4 = state.get_monthly_forecast(date(2024, 3, 10))
    # then:
    assert forecast4.total_income == forecast1.total_income
    assert forecast4.total_expenses == forecast1.total_expenses
    assert forecast4.balance == forecast1.balance
    # and when:
    forecast5 = state.get_monthly_forecast(date(2024, 5, 10))
    # then:
    assert forecast5.total_income == forecast2.total_income
    assert forecast5.total_expenses == forecast2.total_expenses
    assert forecast5.balance == forecast2.balance


def test_financial_state__get_forecast_for_previous_n_months():
    state = FinancialState()
    state.add_entry(
        FinancialEntry(
            amount=Decimal("1000"),
            description="Salary",
            type=EntryType.INCOME,
            category="Income",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2022, 1, 1),
            ),
        )
    )
    state.add_entry(
        FinancialEntry(
            amount=Decimal("600"),
            description="Rent",
            type=EntryType.EXPENSE,
            category="Essentials",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2022, 1, 5),
            ),
        )
    )

    # when:
    forecast = state.get_forecast_for_previous_n_months(3)

    # then:
    assert len(forecast) == 3
    for month_forecast in forecast.values():
        assert month_forecast.total_income == Decimal("1000")
        assert month_forecast.total_expenses == Decimal("600")
        assert month_forecast.balance == Decimal("400")


def test_financial_state__get_forecast_for_next_n_months():
    state = FinancialState()
    state.add_entry(
        FinancialEntry(
            amount=Decimal("2000"),
            description="Salary",
            type=EntryType.INCOME,
            category="Income",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2022, 1, 1),
            ),
        )
    )
    state.add_entry(
        FinancialEntry(
            amount=Decimal("800"),
            description="Rent",
            type=EntryType.EXPENSE,
            category="Essentials",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2022, 1, 5),
            ),
        )
    )

    # when:
    forecast = state.get_forecast_for_next_n_months(6)

    # then:
    assert len(forecast) == 6
    for month_forecast in forecast.values():
        assert month_forecast.total_income == Decimal("2000")
        assert month_forecast.total_expenses == Decimal("800")
        assert month_forecast.balance == Decimal("1200")


def test_financial_state_to_json_file_sets_correct_permissions():
    """Test that to_json_file sets file permissions to 0o600 (owner read/write only)."""
    state = FinancialState()
    state.add_entry(
        FinancialEntry(
            amount=Decimal("1000"),
            description="Test entry",
            type=EntryType.INCOME,
            category="Test",
            recurrence=Recurrence(
                type=RecurrenceType.MONTHLY,
                start_date=date(2024, 1, 1),
            ),
        )
    )

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Save state to file
        state.to_json_file(temp_path)

        # Check file permissions
        file_stats = os.stat(temp_path)
        file_mode = file_stats.st_mode
        # Extract the permission bits (last 3 octal digits)
        permissions = oct(file_mode)[-3:]
        assert permissions == "600", f"Expected 600 permissions, got {permissions}"

        # Verify file content is valid JSON and can be loaded back
        loaded_state = FinancialState.from_json_file(temp_path)
        assert len(loaded_state.income_entries) == 1
        assert loaded_state.income_entries[0].description == "Test entry"

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
