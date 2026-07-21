import api from './axios';
import { ENDPOINTS } from './endpoints';

export const isSafeHeroUrl = (value) => {
  if (typeof value !== 'string' || !value.trim()) return false;
  if (value.startsWith('/') && !value.startsWith('//')) return true;
  try {
    const url = new URL(value);
    const localHttp = url.protocol === 'http:'
      && ['localhost', '127.0.0.1'].includes(url.hostname);
    return (url.protocol === 'https:' || localHttp) && !url.username && !url.password;
  } catch {
    return false;
  }
};

export const adaptHomeHero = (raw) => {
  if (!raw || typeof raw !== 'object') return null;
  if (!['IMAGE', 'VIDEO'].includes(raw.media_type)
    || typeof raw.title !== 'string' || !raw.title.trim()
    || typeof raw.description !== 'string' || !raw.description.trim()) return null;
  const mediaUrl = isSafeHeroUrl(raw.media_url) ? raw.media_url : null;
  if (!mediaUrl) return null;
  return {
    title: raw.title.trim(),
    description: raw.description.trim(),
    mediaType: raw.media_type,
    mediaUrl,
  };
};

export const getHomeHero = ({ signal } = {}) => api.get(
  ENDPOINTS.HOME_HERO, { signal },
).then(({ data, status }) => (status === 204 ? null : adaptHomeHero(data)));

const optionalText = (value) => (
  typeof value === 'string' ? value.trim() : ''
);

export const adaptCustomDressService = (raw) => {
  if (!raw || typeof raw !== 'object') return null;
  const phone = optionalText(raw.whatsapp_phone);
  const message = optionalText(raw.whatsapp_message);
  const steps = Array.isArray(raw.steps)
    ? raw.steps.filter((step) => optionalText(step)).map(optionalText).slice(0, 4)
    : [];
  if (!optionalText(raw.title) || !optionalText(raw.description)
    || !/^[0-9]{8,15}$/.test(phone) || !message || steps.length !== 4) return null;
  return {
    title: optionalText(raw.title),
    description: optionalText(raw.description),
    imageUrl: isSafeHeroUrl(raw.image_url) ? raw.image_url : null,
    whatsappPhone: phone,
    whatsappMessage: message,
    buttonLabel: optionalText(raw.button_label) || 'Continuer sur WhatsApp',
    availabilityText: optionalText(raw.availability_text),
    responseTimeText: optionalText(raw.response_time_text),
    pricingNotice: optionalText(raw.pricing_notice),
    steps,
  };
};

export const getCustomDressService = ({ signal } = {}) => api.get(
  ENDPOINTS.CUSTOM_DRESS_SERVICE, { signal },
).then(({ data, status }) => (
  status === 204 ? null : adaptCustomDressService(data)
));
