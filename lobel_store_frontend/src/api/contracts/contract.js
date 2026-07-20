import { publicConfig } from '../../config/env';

export class ApiContractError extends Error {
  constructor(adapter, field, received) {
    const detail = `${adapter}: champ/structure invalide "${field}".`;
    super(publicConfig.isProduction ? 'Réponse serveur incompatible.' : detail);
    this.name = 'ApiContractError';
    this.code = 'api_contract_error';
    this.adapter = adapter;
    this.field = field;
    this.receivedType = Array.isArray(received) ? 'array' : typeof received;
  }
}

export const requireObject = (value, adapter) => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new ApiContractError(adapter, 'response', value);
  }
  return value;
};

export const requireField = (object, field, adapter) => {
  if (!Object.prototype.hasOwnProperty.call(object, field)) {
    throw new ApiContractError(adapter, field, object);
  }
  return object[field];
};

export const nullableString = (value) => (value == null ? null : String(value));
export const finiteInteger = (value, adapter, field) => {
  const number = Number(value);
  if (!Number.isInteger(number)) throw new ApiContractError(adapter, field, value);
  return number;
};

