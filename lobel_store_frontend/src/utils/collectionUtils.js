export const normalizeApiList = (data) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
};

export const resolveCollectionRef = (collections, slugOrId) => {
  if (!slugOrId || !Array.isArray(collections)) {
    return null;
  }

  return (
    collections.find(
      (collection) =>
        collection.slug === slugOrId || String(collection.id) === String(slugOrId),
    ) ?? null
  );
};

export const productBelongsToCollection = (product, collectionRef) => {
  if (!collectionRef || !product?.collections?.length) {
    return false;
  }

  const targetId = Number(collectionRef.id);
  const targetSlug = collectionRef.slug;

  return product.collections.some((entry) => {
    if (entry == null) {
      return false;
    }

    if (typeof entry === 'object') {
      return entry.id === targetId || entry.slug === targetSlug;
    }

    return Number(entry) === targetId;
  });
};

export const filterProductsByCollectionSlug = (products, collections, slug) => {
  const collectionRef = resolveCollectionRef(collections, slug);

  if (!collectionRef) {
    return [];
  }

  return products.filter((product) => productBelongsToCollection(product, collectionRef));
};
