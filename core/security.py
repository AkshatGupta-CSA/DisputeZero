import re
from typing import Any, Dict

# Regex Patterns
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
# Indian phone numbers start with 6, 7, 8, or 9. This avoids false positives on Unix timestamps (starting with 1).
PHONE_REGEX = re.compile(r'(?<!\d)[6-9]\d{9}(?!\d)')
CARD_REGEX = re.compile(r'(?<!\d)\d{16}(?!\d)')

def mask_pii_value(value: Any) -> Any:
    if isinstance(value, str):
        value = EMAIL_REGEX.sub('[REDACTED_EMAIL]', value)
        value = PHONE_REGEX.sub('[REDACTED_PHONE]', value)
        value = CARD_REGEX.sub('[REDACTED_CARD]', value)
        return value
    elif isinstance(value, dict):
        return {k: mask_pii_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [mask_pii_value(item) for item in value]
    return value

def mask_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively scrubs Personally Identifiable Information (PII) from a dictionary.
    """
    return mask_pii_value(data)
