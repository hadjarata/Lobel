export const adaptResolvedVariant = (raw) => {
  if (!raw || !Number.isInteger(raw.id)) throw new TypeError('invalid_variant');
  if (!Number.isInteger(raw.stock)) throw new TypeError('invalid_stock');
  return {
    id: raw.id,
    product_id: Number(raw.product_id),
    product_name: String(raw.product_name || ''),
    sku: String(raw.sku || ''),
    color: raw.color || null,
    size: raw.size || null,
    attributes: raw.attributes && typeof raw.attributes === 'object' ? raw.attributes : {},
    price: raw.price == null ? null : String(raw.price),
    stock: raw.stock,
    is_available: Boolean(raw.is_available),
    image: raw.image || null,
  };
};

export const availableVariants = (variants) => variants.filter(
  (variant) => variant.is_active !== false && variant.is_available !== false && variant.stock > 0,
);

export const initialVariantSelection = (variants) => {
  const choices = availableVariants(variants);
  return choices.length === 1 ? choices[0].id : null;
};

export const compatibleValues = (variants, selected, attribute) => {
  const choices = availableVariants(variants).filter((variant) => (
    Object.entries(selected).every(([key, value]) => (
      key === attribute || value == null || variant[key]?.id === value
    ))
  ));
  return [...new Map(choices.filter((item) => item[attribute]).map(
    (item) => [item[attribute].id, item[attribute]],
  )).values()];
};

export const findSelectedVariant = (variants, selected) => availableVariants(variants).find(
  (variant) => Object.entries(selected).every(
    ([key, value]) => value == null || variant[key]?.id === value,
  ),
) || null;
