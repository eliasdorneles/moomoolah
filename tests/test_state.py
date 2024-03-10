from datetime import date
from decimal import Decimal

from personal_budget.state import (EntryType, FinancialEntry, FinancialState,
                                   Recurrence, RecurrenceType)


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
    assert forecast.get_balance() == {
        "total_income": Decimal("1000"),
        "total_expenses": Decimal("0"),
        "balance": Decimal("1000"),
    }


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
    assert forecast.get_balance() == {
        "total_income": Decimal("1000"),
        "total_expenses": Decimal("500"),
        "balance": Decimal("500"),
    }
    # when:
    forecast = state.get_monthly_forecast(date(2024, 2, 10))
    # then:
    assert forecast.get_balance() == {
        "total_income": Decimal("1000"),
        "total_expenses": Decimal("500"),
        "balance": Decimal("500"),
    }


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
    assert forecast1.get_balance() == {
        "total_income": Decimal("1000"),
        "total_expenses": Decimal("600"),
        "balance": Decimal("400"),
    }
    # and when:
    forecast2 = state.get_monthly_forecast(date(2024, 2, 10))
    # then:
    assert forecast2.get_balance() == {
        "total_income": Decimal("1000"),
        "total_expenses": Decimal("680"),
        "balance": Decimal("320"),
    }
    # and when:
    forecast3 = state.get_monthly_forecast(date(2024, 3, 10))
    # then:
    assert forecast3.get_balance() == forecast1.get_balance()
    # and when:
    forecast4 = state.get_monthly_forecast(date(2024, 3, 10))
    # then:
    assert forecast4.get_balance() == forecast1.get_balance()
    # and when:
    forecast4 = state.get_monthly_forecast(date(2024, 5, 10))
    # then:
    assert forecast4.get_balance() == forecast2.get_balance()
