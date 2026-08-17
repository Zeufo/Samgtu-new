import pytest

from parse import clean_schedule, faculties_formatter


def test_faculties_formatter():
    with pytest.raises(RuntimeError):
        assert faculties_formatter("")


async def test_clean_schedule():
    assert await clean_schedule(None) == []
    assert await clean_schedule("") == []
