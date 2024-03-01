import enum
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class RecurrenceType(enum.StrEnum):
    ONE_TIME = "ONE_TIME"
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"


class Recurrence(BaseModel):
    start_date: datetime
    type: RecurrenceType
    every: int = 1
    end_date: datetime | None = None

    def will_occur_on_month(self, date: datetime) -> bool:
        if self.type == RecurrenceType.ONE_TIME:
            return self.start_date.month == date.month and self.start_date.year == date.year
        elif self.type == RecurrenceType.MONTHLY:
            return date.month % self.every == self.start_date.month % self.every
        elif self.type == RecurrenceType.ANNUAL:
            return self.start_date.month == date.month


class FinancialEntryType(enum.StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class FinancialEntryCategory(BaseModel):
    name: str
    description: str = ""

    def __hash__(self):
        return hash(self.name)


class FinancialEntry(BaseModel):
    amount: Decimal
    description: str
    type: FinancialEntryType
    recurrence: Recurrence
    category: FinancialEntryCategory


class FinancialState(BaseModel):
    _entries: dict[FinancialEntryType, list[FinancialEntry]] = {
        FinancialEntryType.INCOME: [],
        FinancialEntryType.EXPENSE: [],
    }
    available_categories: dict[FinancialEntryType, set[FinancialEntryCategory]] = {
        FinancialEntryType.INCOME: set(),
        FinancialEntryType.EXPENSE: set(),
    }

    @property
    def income_categories(self) -> set[FinancialEntryCategory]:
        return self.available_categories[FinancialEntryType.INCOME]

    @property
    def expense_categories(self) -> set[FinancialEntryCategory]:
        return self.available_categories[FinancialEntryType.EXPENSE]

    def add_category(self, category: FinancialEntryCategory, entry_type: FinancialEntryType):
        self.available_categories[entry_type].add(category)

    @property
    def income_entries(self) -> list[FinancialEntry]:
        return self._entries[FinancialEntryType.INCOME]

    @property
    def expense_entries(self) -> list[FinancialEntry]:
        return self._entries[FinancialEntryType.EXPENSE]

    def add_entry(self, entry: FinancialEntry):
        if entry.category not in self.available_categories[entry.type]:
            raise ValueError(f"Category {entry.category} is not available for {entry.type} entries")
        self._entries[entry.type].append(entry)

    def remove_entry(self, entry: FinancialEntry):
        self._entries[entry.type].remove(entry)

    def get_forecast_expenses_by_category_for_month(self, month: datetime) -> dict:
        forecast = defaultdict(Decimal)
        for entry in self.expense_entries:
            if entry.recurrence.will_occur_on_month(month):
                forecast[entry.category] += entry.amount
        return forecast

    def get_forecast_income_by_category_for_month(self, month: datetime) -> dict:
        forecast = defaultdict(Decimal)
        for entry in self.income_entries:
            if entry.recurrence.will_occur_on_month(month):
                forecast[entry.category] += entry.amount
        return forecast

    def get_forecast_balance_for_month(self, month: datetime) -> dict[str, Decimal]:
        income = Decimal(sum(self.get_forecast_income_by_category_for_month(month).values()))
        expenses = Decimal(sum(self.get_forecast_expenses_by_category_for_month(month).values()))
        return {
            "income": income,
            "expenses": expenses,
            "balance": income - expenses,
        }

    def get_forecast_balance_for_next_n_months(self, n: int) -> list[dict[str, Decimal]]:
        assert n > 0, "n must be a positive integer"
        forecast = []
        today = datetime.now()
        for i in range(n):
            month = today.replace(month=today.month + i)
            forecast.append({"month": month, "balance": self.get_forecast_balance_for_month(month)})
        return forecast
