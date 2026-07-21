import api from './axios';
import { ENDPOINTS } from './endpoints';
import { adaptPagination, buildListParams } from './pagination';
import { adaptOrderDetail, adaptOrderListItem } from './contracts/orders';

export const getOrders = (filters = {}, config = {}) => api.get(ENDPOINTS.ORDERS, {
  ...config,
  params: buildListParams(filters),
}).then(({ data }) => adaptPagination(data, adaptOrderListItem));

export const getOrderById = (id, config = {}) => api.get(ENDPOINTS.ORDER_DETAIL(id), config)
  .then(({ data }) => adaptOrderDetail(data));

export const cancelOrder = (id, reason) => api.post(
  ENDPOINTS.ORDER_CANCEL(id),
  { reason },
  { skipAuthRefresh: true },
).then(({ data }) => adaptOrderDetail(data));

export const downloadOrderReceipt = (id) => api.get(
  ENDPOINTS.ORDER_RECEIPT(id),
  { responseType: 'blob' },
).then(({ data, headers }) => {
  const contentType = headers['content-type'] || data?.type;
  if (contentType !== 'application/pdf') {
    throw new Error('invalid_receipt_content_type');
  }
  const candidate = headers['content-disposition']
    ?.match(/filename="([A-Za-z0-9._-]+\.pdf)"/)?.[1];
  return {
    blob: data,
    filename: candidate || `lobelstore-justificatif-commande-${id}.pdf`,
  };
});
