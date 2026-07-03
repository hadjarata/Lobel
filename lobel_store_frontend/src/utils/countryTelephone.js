const FALLBACK_COUNTRIES = [
  { label: 'France (+33)', value: 'FR', dialCode: '33' },
  { label: 'Sénégal (+221)', value: 'SN', dialCode: '221' },
  { label: 'Côte d\'Ivoire (+225)', value: 'CI', dialCode: '225' },
  { label: 'Mali (+223)', value: 'ML', dialCode: '223' },
];

const normalizeRow = (item) => {
  if (Array.isArray(item) && item.length >= 3) {
    const [name, iso2, dialCode] = item;

    if (!iso2 || typeof iso2 !== 'string') {
      return null;
    }

    return {
      label: `${name || iso2.toUpperCase()} (+${dialCode || ''})`,
      value: iso2.toUpperCase(),
      dialCode: String(dialCode ?? ''),
    };
  }

  if (item && typeof item === 'object' && item.iso2) {
    return {
      label: `${item.name || item.iso2.toUpperCase()} (+${item.dialCode || ''})`,
      value: String(item.iso2).toUpperCase(),
      dialCode: String(item.dialCode ?? ''),
    };
  }

  return null;
};

export const buildCountryOptions = (rawData) => {
  try {
    const rows = rawData?.allCountries;

    if (!Array.isArray(rows) || rows.length === 0) {
      return [...FALLBACK_COUNTRIES];
    }

    const options = rows
      .map(normalizeRow)
      .filter(Boolean)
      .sort((a, b) => a.label.localeCompare(b.label, 'fr'));

    return options.length > 0 ? options : [...FALLBACK_COUNTRIES];
  } catch {
    return [...FALLBACK_COUNTRIES];
  }
};

export const detectDefaultCountry = (options) => {
  if (!Array.isArray(options) || options.length === 0) {
    return FALLBACK_COUNTRIES[0];
  }

  try {
    const locale = navigator.language || navigator.userLanguage || 'fr-FR';
    const detected = locale.split(/[-_]/)[1]?.toUpperCase();

    if (detected) {
      const match = options.find((option) => option.value === detected);
      if (match) {
        return match;
      }
    }
  } catch {
    // ignore locale detection errors
  }

  return options.find((option) => option.value === 'FR')
    || options.find((option) => option.value === 'SN')
    || options[0];
};
