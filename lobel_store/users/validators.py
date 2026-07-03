import phonenumbers


def normalize_country_code(value):
    if not value:
        return value
    return value.strip().upper()


def validate_country_code(value):
    if not value:
        return value

    value = normalize_country_code(value)
    valid_regions = {
        region
        for regions in phonenumbers.COUNTRY_CODE_TO_REGION_CODE.values()
        for region in regions
    }
    if value not in valid_regions:
        raise ValueError("Le code pays est invalide (ex: SN, FR).")
    return value


def normalize_phone_number(value):
    if not value:
        return ''

    value = value.strip()
    if not value.startswith('+'):
        value = f'+{value}'

    try:
        phone = phonenumbers.parse(value, None)
    except phonenumbers.NumberParseException as exc:
        raise ValueError("Numéro de téléphone invalide.") from exc

    if not phonenumbers.is_valid_number(phone):
        raise ValueError("Numéro de téléphone invalide.")

    return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
