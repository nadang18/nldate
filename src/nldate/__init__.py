from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "a": 1,
    "an": 1,
}

_MONTH_ABBREVIATIONS = (
    "jan",
    "feb",
    "mar",
    "apr",
    "jun",
    "jul",
    "aug",
    "sep",
    "sept",
    "oct",
    "nov",
    "dec",
)


@dataclass(frozen=True)
class _Offset:
    years: int = 0
    months: int = 0
    weeks: int = 0
    days: int = 0

    def scaled(self, factor: int) -> _Offset:
        return _Offset(
            years=self.years * factor,
            months=self.months * factor,
            weeks=self.weeks * factor,
            days=self.days * factor,
        )


def parse(s: str, today: date | None = None) -> date:
    """Parse a common natural-language date expression."""
    reference = today if today is not None else date.today()
    text = _normalize(s)
    if not text:
        raise ValueError("Could not parse empty date expression")

    parsed = _parse_expression(text, reference)
    if parsed is None:
        raise ValueError(f"Could not parse date expression: {s!r}")
    return parsed


def _parse_expression(text: str, today: date) -> date | None:
    simple = _parse_anchor(text, today)
    if simple is not None:
        return simple

    with_prefix = _parse_prefixed_offset(text, today)
    if with_prefix is not None:
        return with_prefix

    with_suffix = _parse_suffixed_offset(text, today)
    if with_suffix is not None:
        return with_suffix

    for connector, sign in ((" before ", -1), (" after ", 1), (" from ", 1)):
        if connector in text:
            amount_text, base_text = text.split(connector, 1)
            offset = _parse_offset(amount_text)
            base = _parse_expression(base_text, today)
            if offset is not None and base is not None:
                return _add_offset(base, offset.scaled(sign))

    return None


def _parse_prefixed_offset(text: str, today: date) -> date | None:
    if not text.startswith("in "):
        return None

    offset = _parse_offset(text.removeprefix("in "))
    if offset is None:
        return None
    return _add_offset(today, offset)


def _parse_suffixed_offset(text: str, today: date) -> date | None:
    if text.endswith(" ago"):
        offset = _parse_offset(text.removesuffix(" ago"))
        if offset is not None:
            return _add_offset(today, offset.scaled(-1))

    if text.endswith(" from now"):
        offset = _parse_offset(text.removesuffix(" from now"))
        if offset is not None:
            return _add_offset(today, offset)

    return None


def _parse_anchor(text: str, today: date) -> date | None:
    if text in {"today", "now"}:
        return today
    if text == "tomorrow":
        return today + timedelta(days=1)
    if text == "yesterday":
        return today - timedelta(days=1)

    weekday = _parse_weekday(text, today)
    if weekday is not None:
        return weekday

    return _parse_concrete_date(text)


def _parse_weekday(text: str, today: date) -> date | None:
    parts = text.split()
    if len(parts) != 2 or parts[1] not in _WEEKDAYS:
        return None

    target = _WEEKDAYS[parts[1]]
    current = today.weekday()
    if parts[0] == "next":
        days = (target - current) % 7
        return today + timedelta(days=days or 7)
    if parts[0] == "last":
        days = (current - target) % 7
        return today - timedelta(days=days or 7)
    if parts[0] == "this":
        return today + timedelta(days=(target - current) % 7)
    return None


def _parse_concrete_date(text: str) -> date | None:
    cleaned = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", text)
    cleaned = _remove_month_abbreviation_periods(cleaned)
    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%B %d, %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%b %d %Y",
    )
    for fmt in formats:
        try:
            if fmt == "%Y-%m-%d":
                return date.fromisoformat(cleaned)
            return _strptime_date(cleaned, fmt)
        except ValueError:
            continue
    return None


def _remove_month_abbreviation_periods(text: str) -> str:
    for month in _MONTH_ABBREVIATIONS:
        text = re.sub(rf"\b{month}\.", month, text)
    return text


def _strptime_date(text: str, fmt: str) -> date:
    import datetime as _datetime

    return _datetime.datetime.strptime(text, fmt).date()


def _parse_offset(text: str) -> _Offset | None:
    remaining = text.replace(",", " ")
    remaining = re.sub(r"\band\b", " ", remaining)
    tokens = remaining.split()
    if len(tokens) % 2 != 0 or not tokens:
        return None

    years = months = weeks = days = 0
    for i in range(0, len(tokens), 2):
        amount = _parse_number(tokens[i])
        unit = tokens[i + 1].removesuffix("s")
        if amount is None:
            return None
        if unit == "year":
            years += amount
        elif unit == "month":
            months += amount
        elif unit == "week":
            weeks += amount
        elif unit == "day":
            days += amount
        else:
            return None

    return _Offset(years=years, months=months, weeks=weeks, days=days)


def _parse_number(text: str) -> int | None:
    if text.isdecimal():
        return int(text)
    return _NUMBER_WORDS.get(text)


def _add_offset(start: date, offset: _Offset) -> date:
    month_index = (
        start.year * 12 + (start.month - 1) + offset.years * 12 + offset.months
    )
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    shifted = date(year, month, day)
    return shifted + timedelta(weeks=offset.weeks, days=offset.days)


def _normalize(text: str) -> str:
    return " ".join(text.casefold().strip().split())


def main() -> None:
    print(parse("today"))
