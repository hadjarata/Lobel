import { resolveMediaUrl } from '../config/api';

export const normalizeMediaUrl = resolveMediaUrl;

export const getProductImageUrl = (product) => {
  if (!product) {
    return null;
  }

  if (product.image) {
    return normalizeMediaUrl(product.image);
  }

  const mediaFiles = product.media_files;
  if (Array.isArray(mediaFiles) && mediaFiles.length > 0) {
    const firstImage =
      mediaFiles.find((media) => media.media_type === 'image') || mediaFiles[0];

    if (firstImage) {
      return normalizeMediaUrl(firstImage.url || firstImage.file_url || firstImage.file);
    }
  }

  return null;
};
