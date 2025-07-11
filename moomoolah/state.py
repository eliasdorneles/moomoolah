import enum
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import NamedTuple

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field


class CurrencyFormat(NamedTuple):
    symbol: str
    code: str
    decimal_places: int
    decimal_separator: str
    thousands_separator: str


CURRENCY_FORMATS = {
    "EUR": CurrencyFormat("€", "EUR", 2, ".", ","),
    "USD": CurrencyFormat("$", "USD", 2, ".", ","),
    "GBP": CurrencyFormat("£", "GBP", 2, ".", ","),
    "JPY": CurrencyFormat("¥", "JPY", 0, ".", ","),
    "CAD": CurrencyFormat("C$", "CAD", 2, ".", ","),
    "AUD": CurrencyFormat("A$", "AUD", 2, ".", ","),
    "BRL": CurrencyFormat("R$", "BRL", 2, ",", "."),
    "TL": CurrencyFormat("₺", "TL", 2, ",", "."),
}


def format_currency(amount: Decimal, currency_code: str) -> str:
    """Format a decimal amount with the appropriate currency symbol and formatting."""
    fmt = CURRENCY_FORMATS[currency_code]

    # Round to appropriate decimal places
    if fmt.decimal_places == 0:
        amount = amount.quantize(Decimal("1"))
    else:
        amount = amount.quantize(Decimal("0.01"))

    # Convert to string and split into integer and decimal parts
    amount_str = str(amount)
    if "." in amount_str:
        integer_part, decimal_part = amount_str.split(".")
    else:
        integer_part, decimal_part = amount_str, ""

    # Handle negative sign
    negative_sign = ""
    if integer_part.startswith("-"):
        negative_sign = "-"
        integer_part = integer_part[1:]

    # Add thousands separators
    if len(integer_part) > 3:
        # Add thousands separator from right to left
        formatted_integer = ""
        for i, digit in enumerate(reversed(integer_part)):
            if i > 0 and i % 3 == 0:
                formatted_integer = fmt.thousands_separator + formatted_integer
            formatted_integer = digit + formatted_integer
        integer_part = formatted_integer

    # Construct final formatted string
    if fmt.decimal_places > 0 and decimal_part:
        # Pad decimal part to required length
        decimal_part = decimal_part.ljust(fmt.decimal_places, "0")
        formatted_amount = (
            f"{negative_sign}{integer_part}{fmt.decimal_separator}{decimal_part}"
        )
    elif fmt.decimal_places > 0:
        # Add decimal separator with zeros
        formatted_amount = f"{negative_sign}{integer_part}{fmt.decimal_separator}{'0' * fmt.decimal_places}"
    else:
        formatted_amount = f"{negative_sign}{integer_part}"

    return f"{fmt.symbol}{formatted_amount}"


def to_ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


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
            if self.end_date and month_date > self.end_date:
                return False
            if (
                month_date.year <= self.start_date.year
                and month_date.month < self.start_date.month
            ):
                return False
            return month_date.month % self.every == self.start_date.month % self.every
        elif self.type == RecurrenceType.ANNUAL:
            return self.start_date.month == month_date.month
        raise ValueError(f"Invalid recurrence type: {self.type}")

    @property
    def description(self) -> str:
        if self.type == RecurrenceType.ONE_TIME:
            return f"Once on {self.start_date}"
        elif self.type == RecurrenceType.MONTHLY and self.every == 1:
            return f"Monthly on the {to_ordinal(self.start_date.day)}"
        elif self.type == RecurrenceType.MONTHLY:
            return f"Every {self.every} months on the {to_ordinal(self.start_date.day)}"
        elif self.type == RecurrenceType.ANNUAL:
            return f"Annually on the {to_ordinal(self.start_date.day)} of {self.start_date.strftime('%B')}"
        raise ValueError(f"Invalid recurrence type: {self.type}")


class EntryType(enum.StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class FinancialEntry(BaseModel):
    amount: Decimal = Decimal(0)
    description: str = ""
    type: EntryType = EntryType.EXPENSE
    recurrence: Recurrence = Field(
        default_factory=lambda: Recurrence(
            type=RecurrenceType.MONTHLY, start_date=date.today()
        )
    )
    category: str = "Essentials"

    def will_occur_on_month(self, month: date) -> bool:
        return self.recurrence.will_occur_on_month(month)


class MonthlyForecast(BaseModel):
    month: date
    expenses_by_category: dict[str, Decimal]
    income_by_category: dict[str, Decimal]

    @property
    def total_income(self) -> Decimal:
        return Decimal(sum(self.income_by_category.values()))

    @property
    def total_expenses(self) -> Decimal:
        return Decimal(sum(self.expenses_by_category.values()))

    @property
    def balance(self) -> Decimal:
        return self.total_income - self.total_expenses

    @classmethod
    def from_financial_entries(
        cls,
        month: date,
        income_entries: list[FinancialEntry],
        expenses_entries: list[FinancialEntry],
    ) -> "MonthlyForecast":
        def _build_forecast_by_category_for_month(
            entries: list[FinancialEntry],
        ) -> dict:
            forecast = defaultdict(Decimal)
            for entry in entries:
                if entry.will_occur_on_month(month):
                    forecast[entry.category] += entry.amount
            return forecast

        return cls(
            month=month,
            expenses_by_category=_build_forecast_by_category_for_month(
                expenses_entries
            ),
            income_by_category=_build_forecast_by_category_for_month(income_entries),
        )


class FinancialState(BaseModel):
    all_entries: dict[EntryType, list[FinancialEntry]] = {
        EntryType.INCOME: [],
        EntryType.EXPENSE: [],
    }
    currency_code: str = "EUR"

    @property
    def income_entries(self) -> list[FinancialEntry]:
        return self.all_entries[EntryType.INCOME]

    @property
    def expense_entries(self) -> list[FinancialEntry]:
        return self.all_entries[EntryType.EXPENSE]

    @property
    def categories_per_type(self) -> dict[EntryType, set[str]]:
        return {
            EntryType.INCOME: {entry.category for entry in self.income_entries},
            EntryType.EXPENSE: {entry.category for entry in self.expense_entries},
        }

    def add_entry(self, entry: FinancialEntry):
        self.all_entries[entry.type].append(entry)

    def remove_entry(self, entry: FinancialEntry):
        self.all_entries[entry.type].remove(entry)

    def get_monthly_forecast(self, month: date) -> MonthlyForecast:
        return MonthlyForecast.from_financial_entries(
            month, self.income_entries, self.expense_entries
        )

    def get_forecast_for_next_n_months(self, n: int) -> dict[date, MonthlyForecast]:
        assert n > 0, "n must be a positive integer"
        forecast: dict[date, MonthlyForecast] = {}
        today = date.today()
        for i in range(n):
            month = today + relativedelta(months=i)
            forecast[month] = self.get_monthly_forecast(month)
        return forecast

    def get_forecast_for_previous_n_months(self, n: int) -> dict[date, MonthlyForecast]:
        assert n > 0, "n must be a positive integer"
        forecast: dict[date, MonthlyForecast] = {}
        today = date.today()
        for i in range(1, n + 1):
            month = today - relativedelta(months=i)
            forecast[month] = self.get_monthly_forecast(month)
        return forecast

    def get_entries_for_month(self, month: date) -> list[FinancialEntry]:
        """Get all individual financial entries that occur in a specific month."""
        entries = []
        for entry in self.income_entries + self.expense_entries:
            if entry.will_occur_on_month(month):
                entries.append(entry)
        return entries

    @classmethod
    def from_json_file(cls, file_path: str) -> "FinancialState":
        with open(file_path, "r") as file:
            return cls.model_validate_json(file.read())

    def to_json_file(self, file_path: str):
        import os

        with open(file_path, "w") as file:
            file.write(self.model_dump_json(indent=2))
        # Set file permissions to be readable/writable by owner only
        os.chmod(file_path, 0o600)
