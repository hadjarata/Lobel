import { useEffect, useRef, useState } from 'react';
import { getProducts } from '../api/products';
import { normalizeApiError } from '../utils/apiErrors';
import { createLatestRequest } from './latestRequest';
import { catalogPriceError, toProductListParams } from './catalogQuery';

const INITIAL = { products: [], count: 0, loading: true, error: null };

export const useCatalogProducts = (query, retryKey = 0) => {
  const [state, setState] = useState(INITIAL);
  const runner = useRef(null);
  if (!runner.current) runner.current = createLatestRequest();
  const key = JSON.stringify(query);

  useEffect(() => {
    const priceError = catalogPriceError(query);
    if (priceError) {
      setState({ products: [], count: 0, loading: false, error: priceError });
      return undefined;
    }
    let mounted = true;
    setState((previous) => ({ ...previous, products: [], loading: true, error: null }));
    runner.current.run((signal) => getProducts(toProductListParams(query), { signal }))
      .then((result) => {
        if (mounted && result.current) {
          setState({
            products: result.value.results,
            count: result.value.count,
            loading: false,
            error: null,
          });
        }
      })
      .catch((error) => {
        const normalized = normalizeApiError(error, 'Impossible de charger le catalogue.');
        if (mounted && !normalized.isCanceled) {
          setState({ products: [], count: 0, loading: false, error: normalized.message });
        }
      });
    return () => {
      mounted = false;
      runner.current.cancel();
    };
  // key intentionally captures the normalized query as one dependency.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, retryKey]);

  return state;
};

