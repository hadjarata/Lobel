import { finiteInteger, nullableString, requireField, requireObject } from './contract';

export const adaptCustomer = (raw) => {
  const data = requireObject(raw, 'customer');
  const user = requireObject(requireField(data, 'user', 'customer'), 'customer.user');
  return {
    id: finiteInteger(requireField(data, 'id', 'customer'), 'customer', 'id'),
    user: {
      id: finiteInteger(requireField(user, 'id', 'customer.user'), 'customer.user', 'id'),
      username: String(requireField(user, 'username', 'customer.user')),
      first_name: nullableString(user.first_name) || '',
      last_name: nullableString(user.last_name) || '',
      email: String(requireField(user, 'email', 'customer.user')),
      is_active: Boolean(user.is_active),
    },
    country: nullableString(data.country) || '',
    phone_number: nullableString(data.phone_number) || '',
    address: nullableString(data.address) || '',
    date_created: nullableString(data.date_created),
  };
};

