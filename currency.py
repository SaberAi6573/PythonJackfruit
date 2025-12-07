# ---------------- CURRENCY (AUTO FROM TIMEZONES + HISTORY, WITH ALIASES) ---------------- #
import requests  # RestCountries + Frankfurter client.
import pytz  # Provides canonical timezone lists grouped by ISO country.


def _load_aliases(file_path):  # Helper to load alias mappings at import time.
	"""Load timezone aliases from a simple key=value file."""  # Describe the expected file format.

	aliases = {}  # Local dict for storing parsed aliases.

	try:  # Attempt to open the alias file.
		alias_file = open(file_path, "r", encoding="utf-8")  # Open once; caller handles absence via except.
	except FileNotFoundError:  # Silently ignore missing alias file.
		return aliases  # Return empty mapping when aliases are unavailable.

	with alias_file:  # Ensure file descriptor closes automatically.
		for line in alias_file:  # Iterate each row to parse entries.
			line = line.strip()  # Ignore whitespace padding around entries.
			if not line or line.startswith("#") or "=" not in line:  # Skip blanks/comments/invalid rows.
				continue  # Continue scanning remaining lines.
			alias, canonical = line.split("=", 1)  # Only split on the first '='.
			aliases[alias.strip()] = canonical.strip()  # Store trimmed alias pair.

	return aliases  # Provide the parsed alias dictionary to the caller.


ALIAS_FILE = "tz_aliases.txt"  # Default alias file bundled with the project.
TZ_ALIAS_MAP = _load_aliases(ALIAS_FILE)  # Parse aliases immediately during module load.

# Build timezone -> country once at import time
TIMEZONE_TO_COUNTRY = {}  # Holds canonical timezone to country code mappings.
for country_code, zones in pytz.country_timezones.items():  # Walk each ISO country entry.
	for zone in zones:  # Associate each timezone with its owning country.
		TIMEZONE_TO_COUNTRY[zone] = country_code  # Canonical mapping straight from pytz.

# Layer aliases onto the same dict (they inherit the canonical country)
for alias, canonical in TZ_ALIAS_MAP.items():  # Iterate any configured alias entries.
	country_code = TIMEZONE_TO_COUNTRY.get(canonical)  # Look up the canonical country.
	if country_code:  # Only register alias when canonical mapping exists.
		TIMEZONE_TO_COUNTRY[alias] = country_code  # Aliases piggyback on canonical ownership.

COUNTRY_TO_CURRENCY_CACHE = {}  # Avoid repeated RestCountries hits.


def get_currency_from_country(country_code):  # Look up the ISO currency for a country.
	"""Return the primary currency for `country_code`, caching results per run."""  # Document the caching behavior.

	country_code = country_code.upper()  # Normalize to uppercase for cache consistency.

	if country_code in COUNTRY_TO_CURRENCY_CACHE:  # Serve cached lookups immediately.
		return COUNTRY_TO_CURRENCY_CACHE[country_code]  # Return memoized currency code.

	url = f"https://restcountries.com/v3.1/alpha/{country_code}"  # Build RestCountries endpoint.
	resp = requests.get(url, timeout=10)  # External lookup for currency metadata.
	resp.raise_for_status()  # Raise if API responded with an error status.

	data = resp.json()  # Decode JSON payload.

	if not data:  # Empty response means the country code was invalid.
		raise ValueError(f"No country info found for code: {country_code}")  # Surface invalid code.

	info = data[0]  # Use the first (and only) object returned.
	currencies = info.get("currencies", {})  # Pull currency dictionary.

	if not currencies:  # Guard against missing currency block.
		raise ValueError(f"No currency info for country code: {country_code}")  # Inform caller of missing data.

	currency_code = next(iter(currencies.keys()))  # Take the first listed currency.
	COUNTRY_TO_CURRENCY_CACHE[country_code] = currency_code  # Cache for future calls.

	return currency_code  # Return ISO currency code string.


def get_currency_from_timezone(tz_name):  # Resolve timezone to currency via country mapping.
	"""Map a timezone (canonical or alias) to the owning country's currency."""  # Explain behavior for aliases.

	country_code = TIMEZONE_TO_COUNTRY.get(tz_name)  # Translate timezone to ISO country code.

	if not country_code:  # Fail when timezone is unknown.
		raise ValueError(f"Cannot detect country for timezone: {tz_name}")  # Notify caller about invalid timezone.

	return get_currency_from_country(country_code)  # Delegate to country-level lookup.


def convert_currency(amount, from_cur, to_cur, date_str=None):  # Convert between currencies via Frankfurter.
	"""Convert `amount` via Frankfurter, using `date_str` for historical rates when provided."""  # Outline historical rate support.

	try:  # Validate amount input eagerly.
		amount_value = float(amount)  # Accept strings or numerics; fail fast otherwise.
	except (TypeError, ValueError) as exc:  # Catch conversion issues.
		raise ValueError("Amount must be a numeric value.") from exc  # Reraise with clearer message.

	if not from_cur or not to_cur:  # Ensure both currencies exist.
		raise ValueError("Both source and target currency codes are required.")  # Prompt for missing code.

	from_cur = from_cur.strip().upper()  # Normalize source currency formatting.
	to_cur = to_cur.strip().upper()  # Normalize target currency formatting.

	if from_cur == to_cur:  # No conversion needed when both match.
		return amount_value, "same currency"  # Return passthrough amount and note.

	base_url = "https://api.frankfurter.app"  # Base API endpoint.
	url = f"{base_url}/{date_str}" if date_str else f"{base_url}/latest"  # Historical vs latest route.

	params = {  # Build query parameter payload for Frankfurter.
		"amount": amount_value,  # Quantity to convert.
		"from": from_cur,  # Base currency code.
		"to": to_cur,  # Quote currency code.
	}

	resp = requests.get(url, params=params, timeout=10)  # Execute Frankfurter request.
	resp.raise_for_status()  # Raise errors for non-2xx responses.

	data = resp.json()  # Parse the conversion payload.
	rates = data.get("rates", {})  # Extract rate mappings.

	if to_cur not in rates:  # API did not supply requested quote.
		raise ValueError(f"No rate found for {to_cur} on {data.get('date', date_str)}")  # Communicate missing rate.

	converted = rates[to_cur]  # Grab the converted amount.
	date_used = data.get("date", date_str or "unknown date")  # Track which date backed the rate.

	return converted, date_used  # Provide both converted value and rate date.
