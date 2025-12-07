# ---------------- CURRENCY (AUTO FROM TIMEZONES + HISTORY, WITH ALIASES) ---------------- #
import requests  # RestCountries + Frankfurter client.
import pytz  # Provides canonical timezone lists grouped by ISO country.


def _load_aliases(file_path):
    """Load timezone aliases from a simple key=value file."""
    aliases = {}
    try:
        alias_file = open(file_path, "r", encoding="utf-8")  # Open once; caller handles absence via except.
    except FileNotFoundError:
        return aliases

    with alias_file:
        for line in alias_file:
            line = line.strip()  # Ignore whitespace padding around entries.
            if not line or line.startswith("#") or "=" not in line:
                continue
            alias, canonical = line.split("=", 1)  # Only split on the first '='.
            aliases[alias.strip()] = canonical.strip()  # Store trimmed alias pair.
    return aliases


ALIAS_FILE = "tz_aliases.txt"
TZ_ALIAS_MAP = _load_aliases(ALIAS_FILE)

# Build timezone -> country once at import time
TIMEZONE_TO_COUNTRY = {}
for country_code, zones in pytz.country_timezones.items():
    for zone in zones:
        TIMEZONE_TO_COUNTRY[zone] = country_code  # Canonical mapping straight from pytz.

# Layer aliases onto the same dict (they inherit the canonical country)
for alias, canonical in TZ_ALIAS_MAP.items():
    country_code = TIMEZONE_TO_COUNTRY.get(canonical)
    if country_code:
        TIMEZONE_TO_COUNTRY[alias] = country_code  # Aliases piggyback on canonical ownership.

COUNTRY_TO_CURRENCY_CACHE = {}  # Avoid repeated RestCountries hits.


def get_currency_from_country(country_code):
    """Return the primary currency for `country_code`, caching results per run."""
    country_code = country_code.upper()
    if country_code in COUNTRY_TO_CURRENCY_CACHE:
        return COUNTRY_TO_CURRENCY_CACHE[country_code]

    url = f"https://restcountries.com/v3.1/alpha/{country_code}"
    resp = requests.get(url, timeout=10)  # External lookup for currency metadata.
    resp.raise_for_status()

    data = resp.json()
    if not data:
        raise ValueError(f"No country info found for code: {country_code}")

    info = data[0]
    currencies = info.get("currencies", {})
    if not currencies:
        raise ValueError(f"No currency info for country code: {country_code}")

    currency_code = next(iter(currencies.keys()))  # Take the first listed currency.
    COUNTRY_TO_CURRENCY_CACHE[country_code] = currency_code
    return currency_code


def get_currency_from_timezone(tz_name):
    """Map a timezone (canonical or alias) to the owning country's currency."""
    country_code = TIMEZONE_TO_COUNTRY.get(tz_name)
    if not country_code:
        raise ValueError(f"Cannot detect country for timezone: {tz_name}")
    return get_currency_from_country(country_code)


def convert_currency(amount, from_cur, to_cur, date_str=None):
    """Convert `amount` via Frankfurter, using `date_str` for historical rates when provided."""
    try:
        amount_value = float(amount)  # Accept strings or numerics; fail fast otherwise.
    except (TypeError, ValueError) as exc:
        raise ValueError("Amount must be a numeric value.") from exc

    if not from_cur or not to_cur:
        raise ValueError("Both source and target currency codes are required.")
    from_cur = from_cur.strip().upper()
    to_cur = to_cur.strip().upper()
    if from_cur == to_cur:
        return amount_value, "same currency"

    base_url = "https://api.frankfurter.app"
    url = f"{base_url}/{date_str}" if date_str else f"{base_url}/latest"

    params = {
        "amount": amount_value,
        "from": from_cur,
        "to": to_cur,
    }

    resp = requests.get(url, params=params, timeout=10)  # Execute Frankfurter request.
    resp.raise_for_status()

    data = resp.json()
    rates = data.get("rates", {})
    if to_cur not in rates:
        raise ValueError(f"No rate found for {to_cur} on {data.get('date', date_str)}")
    converted = rates[to_cur]
    date_used = data.get("date", date_str or "unknown date")
    return converted, date_used