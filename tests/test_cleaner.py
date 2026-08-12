import pytest

from parse import faculties_formatter


def test_faculties_formatter():
    with pytest.raises(RuntimeError):
        assert faculties_formatter("")
