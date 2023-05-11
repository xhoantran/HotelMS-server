import pytest

from ..currency import get_currency_min_frac_size, is_valid_currency


def test_currency():
    assert is_valid_currency("USD")
    assert is_valid_currency("VND")
    assert not is_valid_currency("ABC")
    assert get_currency_min_frac_size("USD") == 100
    assert get_currency_min_frac_size("VND") == 1

    with pytest.raises(ValueError):
        get_currency_min_frac_size("ABC")
