import { resolveMediaUrl } from '../../config/api';
import {
  ApiContractError,
  finiteInteger,
  nullableString,
  requireField,
  requireObject,
} from './contract';

export const adaptCategory = (raw) => {
  const data = requireObject(raw, 'category');
  return {
    id: finiteInteger(requireField(data, 'id', 'category'), 'category', 'id'),
    name: String(requireField(data, 'name', 'category')),
    description: nullableString(data.description) || '',
    is_active: Boolean(data.is_active),
    date_created: nullableString(data.date_created),
  };
};

export const adaptCollection = (raw) => {
  const data = requireObject(raw, 'collection');
  const slug = requireField(data, 'slug', 'collection');
  if (typeof slug !== 'string' || !slug) throw new ApiContractError('collection', 'slug', slug);
  return {
    ...data,
    id: finiteInteger(requireField(data, 'id', 'collection'), 'collection', 'id'),
    slug,
    name: String(requireField(data, 'name', 'collection')),
    description: nullableString(data.description) || '',
    image_url: resolveMediaUrl(data.image_url || data.image),
    video_url: resolveMediaUrl(data.video_url || data.video),
    products: Array.isArray(data.products) ? data.products : [],
  };
};

export const adaptVariant = (raw) => {
  const data = requireObject(raw, 'variant');
  return {
    id: finiteInteger(requireField(data, 'id', 'variant'), 'variant', 'id'),
    color: data.color ? { ...data.color } : null,
    size: data.size ? { ...data.size } : null,
    stock: finiteInteger(requireField(data, 'stock', 'variant'), 'variant', 'stock'),
    is_active: Boolean(data.is_active),
    sku: nullableString(data.sku) || '',
    price: data.price == null ? null : String(data.price),
  };
};

export const adaptMedia = (raw) => {
  const data = requireObject(raw, 'product-media');
  const url = requireField(data, 'url', 'product-media');
  return {
    id: finiteInteger(requireField(data, 'id', 'product-media'), 'product-media', 'id'),
    media_type: String(requireField(data, 'media_type', 'product-media')),
    type: String(data.media_type),
    url: resolveMediaUrl(url),
    order: Number(data.order) || 0,
    width: data.width ?? null,
    height: data.height ?? null,
    duration_seconds: data.duration_seconds ?? null,
  };
};

const adaptProductBase = (raw, adapter) => {
  const data = requireObject(raw, adapter);
  return {
    ...data,
    id: finiteInteger(requireField(data, 'id', adapter), adapter, 'id'),
    name: String(requireField(data, 'name', adapter)),
    price: requireField(data, 'price', adapter) == null ? null : String(data.price),
    category: adaptCategory(requireField(data, 'category', adapter)),
    collections: Array.isArray(data.collections) ? data.collections : [],
    variants: Array.isArray(data.variants) ? data.variants.map(adaptVariant) : [],
    image: resolveMediaUrl(data.image),
    is_available: Boolean(data.is_available),
    date_created: nullableString(data.date_created),
  };
};

export const adaptProductListItem = (raw) => adaptProductBase(raw, 'product-list');
export const adaptProductDetail = (raw) => {
  const product = adaptProductBase(raw, 'product-detail');
  const mediaFiles = Array.isArray(raw.media_files) ? raw.media_files.map(adaptMedia) : [];
  return {
    ...product,
    description: nullableString(raw.description) || '',
    is_active: Boolean(requireField(raw, 'is_active', 'product-detail')),
    media_files: mediaFiles,
    media: mediaFiles,
    video: resolveMediaUrl(raw.video),
  };
};

