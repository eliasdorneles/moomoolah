import enum
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class RecurrenceType(enum.StrEnum):
    ONE_TIME = "ONE_TIME"
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"


class Recurrence(BaseModel):
    start_date: date
    type: RecurrenceType
    every: int = 1
    end_date: date | None = None

    def will_occur_on_month(self, month_date: date) -> bool:
        if self.type == RecurrenceType.ONE_TIME:
            return (
                self.start_date.month == month_date.month
                and self.start_date.year == month_date.year
            )
        elif self.type == RecurrenceType.MONTHLY:
            return month_date.month % self.every == self.start_date.month % self.every
        elif self.type == RecurrenceType.ANNUAL:
            return self.start_date.month == month_date.month
        raise ValueError(f"Invalid recurrence type: {self.type}")


class EntryType(enum.StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class FinancialEntry(BaseModel):
    amount: Decimal
    description: str
    type: EntryType
    recurrence: Recurrence
    category: str

    def will_occur_on_month(self, month: date) -> bool:
        return self.recurrence.will_occur_on_month(month)


class MonthlyForecast(BaseModel):
    month: date
    expenses_by_category: dict[str, Decimal]
    income_by_category: dict[str, Decimal]

    def get_balance(self) -> dict[str, Decimal]:
        income = Decimal(sum(self.income_by_category.values()))
        expenses = Decimal(sum(self.expenses_by_category.values()))
        return {
            "total_income": income,
            "total_expenses": expenses,
            "balance": income - expenses,
        }

    @classmethod
    def from_financial_entries(
        cls,
        month: date,
        income_entries: list[FinancialEntry],
        expenses_entries: list[FinancialEntry],
    ) -> "MonthlyForecast":
        def _build_forecast_by_category_for_month(entries: list[FinancialEntry]) -> dict:
            forecast = defaultdict(Decimal)
            for entry in entries:
                if entry.will_occur_on_month(month):
                    forecast[entry.category] += entry.amount
            return forecast

        return cls(
            month=month,
            expenses_by_category=_build_forecast_by_category_for_month(expenses_entries),
            income_by_category=_build_forecast_by_category_for_month(income_entries),
        )


class FinancialState(BaseModel):
    _entries: dict[EntryType, list[FinancialEntry]] = {
        EntryType.INCOME: [],
        EntryType.EXPENSE: [],
    }
    _available_categories: dict[EntryType, set[str]] = {
        EntryType.INCOME: set(),
        EntryType.EXPENSE: set(),
    }

    @property
    def income_categories(self) -> set[str]:
        return self._available_categories[EntryType.INCOME]

    @property
    def expense_categories(self) -> set[str]:
        return self._available_categories[EntryType.EXPENSE]

    def add_category(self, entry_type: EntryType, category: str):
        self._available_categories[entry_type].add(category)

    @property
    def income_entries(self) -> list[FinancialEntry]:
        return self._entries[EntryType.INCOME]

    @property
    def expense_entries(self) -> list[FinancialEntry]:
        return self._entries[EntryType.EXPENSE]

    def add_entry(self, entry: FinancialEntry):
        self._available_categories[entry.type].add(entry.category)
        self._entries[entry.type].append(entry)

    def remove_entry(self, entry: FinancialEntry):
        self._entries[entry.type].remove(entry)

    def get_monthly_forecast(self, month: date) -> MonthlyForecast:
        return MonthlyForecast.from_financial_entries(
            month, self.income_entries, self.expense_entries
        )

    def get_forecast_for_next_n_months(self, n: int) -> dict[str, MonthlyForecast]:
        assert n > 0, "n must be a positive integer"
        forecast: dict[str, MonthlyForecast] = {}
        today = date.today()
        for i in range(n):
            month = today.replace(month=today.month + i)
            forecast[f"{month.year}-{month.month}"] = self.get_monthly_forecast(month)
        return forecast
