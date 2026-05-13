from datetime import date

import pytest

from nldate import parse

REFERENCE = date(2025, 11, 5)  # Wednesday


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("today", date(2025, 11, 5)),
        ("tomorrow", date(2025, 11, 6)),
        ("yesterday", date(2025, 11, 4)),
        ("in 3 days", date(2025, 11, 8)),
        ("3 days from now", date(2025, 11, 8)),
        ("2 weeks ago", date(2025, 10, 22)),
        ("next Tuesday", date(2025, 11, 11)),
        ("last Friday", date(2025, 10, 31)),
        ("December 1st, 2025", date(2025, 12, 1)),
        ("2025-12-01", date(2025, 12, 1)),
        ("12/1/2025", date(2025, 12, 1)),
        ("5 days before December 1st, 2025", date(2025, 11, 26)),
        ("1 year and 2 months after yesterday", date(2027, 1, 4)),
        ("two weeks from tomorrow", date(2025, 11, 20)),
    ],
)
def test_parse_common_date_phrases(text: str, expected: date) -> None:
    assert parse(text, today=REFERENCE) == expected


def test_parse_is_case_and_whitespace_insensitive() -> None:
    assert parse("  NEXT    tuesday  ", today=REFERENCE) == date(2025, 11, 11)


def test_parse_rejects_unknown_input() -> None:
    with pytest.raises(ValueError, match="Could not parse"):
        parse("someday soon", today=REFERENCE)
