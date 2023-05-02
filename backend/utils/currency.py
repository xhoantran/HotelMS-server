CURRENCY_MIN_FRAC_SIZE = {
    "USD": 100,
    "VND": 1,
}


def is_valid_currency(currency):
    return currency in CURRENCY_MIN_FRAC_SIZE


def get_currency_min_frac_size(currency):
    if not is_valid_currency(currency):
        raise ValueError(f"Invalid currency: {currency}")
    return CURRENCY_MIN_FRAC_SIZE[currency]
