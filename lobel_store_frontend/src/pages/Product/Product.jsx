import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getProductById, getProducts } from '../../api/products';
import ProductGallery from '../../components/product/ProductGallery';
import ProductGrid from '../../components/product/ProductGrid';
import AddToCartButton from '../../components/product/AddToCartButton';
import { normalizeApiError } from '../../utils/apiErrors';
import { useCart } from '../../cart/cartState';
import { initialVariantSelection } from '../../cart/variantModel';
import './Product.css';

const Product = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addItem } = useCart();
  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [selectedColorId, setSelectedColorId] = useState(null);
  const [selectedSizeId, setSelectedSizeId] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setProduct(null);
    getProductById(id, { signal: controller.signal })
      .then(async (data) => {
        setProduct(data);
        const selectedId = initialVariantSelection(data.variants);
        const selected = data.variants.find((variant) => variant.id === selectedId);
        setSelectedColorId(selected?.color?.id ?? null);
        setSelectedSizeId(selected?.size?.id ?? null);
        const page = await getProducts(
          { category: data.category.id, page_size: 5 },
          { signal: controller.signal },
        );
        setRelated(page.results.filter((item) => item.id !== data.id).slice(0, 4));
      })
      .catch((requestError) => {
        const normalized = normalizeApiError(requestError, 'Produit introuvable.');
        if (!normalized.isCanceled) setError(normalized.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [id]);

  const variants = useMemo(
    () => product?.variants.filter((variant) => variant.is_active) || [],
    [product],
  );
  const colors = useMemo(() => [
    ...new Map(variants.filter(({ color }) => color).map(({ color }) => [color.id, color])).values(),
  ], [variants]);
  const sizes = useMemo(() => [
    ...new Map(variants.filter(({ size }) => size).map(({ size }) => [size.id, size])).values(),
  ], [variants]);
  const selectedVariant = variants.find(
    ({ color, size }) => (color?.id ?? null) === selectedColorId && (size?.id ?? null) === selectedSizeId,
  );

  const selectColor = (colorId) => {
    setSelectedColorId(colorId);
    const compatible = variants.find(
      ({ color, size, stock }) => color?.id === colorId && stock > 0
        && (size?.id ?? null) === selectedSizeId,
    ) || variants.find(({ color, stock }) => color?.id === colorId && stock > 0);
    if (compatible) setSelectedSizeId(compatible.size?.id ?? null);
    setQuantity(1);
  };

  const handleAdd = async () => {
    if (!selectedVariant || selectedVariant.stock < 1) return;
    setAdding(true);
    try {
      await addItem({
        ...selectedVariant,
        product_id: product.id,
        product_name: product.name,
        is_available: selectedVariant.is_active && selectedVariant.stock > 0,
      }, quantity);
    } catch (requestError) {
      setError(normalizeApiError(requestError, 'Impossible d’ajouter ce produit.').message);
    } finally {
      setAdding(false);
    }
  };

  if (loading) return <main className="product-page"><div className="product-loading">Chargement…</div></main>;
  if (error && !product) {
    return <main className="product-page"><div className="product-error" role="alert"><p>{error}</p><button onClick={() => navigate('/shop')}>Retour à la boutique</button></div></main>;
  }
  if (!product) return null;

  const price = Number(selectedVariant?.price ?? product.price);
  return (
    <main className="product-page">
      <div className="product-container">
        <nav className="product-breadcrumb" aria-label="Fil d’Ariane">
          <button type="button" onClick={() => navigate('/')}>Accueil</button>
          <span aria-hidden="true">/</span>
          <button type="button" onClick={() => navigate('/shop')}>Boutique</button>
          <span aria-hidden="true">/</span>
          <span aria-current="page">{product.name}</span>
        </nav>
        <div className="product-main">
          <div className="product-gallery-section">
            <ProductGallery media={product.media_files} productName={product.name} />
          </div>
          <div className="product-info-section">
            <h1 className="product-title">{product.name}</h1>
            <p className="product-price">{price.toLocaleString('fr-FR')} FCFA</p>
            <p className="product-description">{product.description}</p>
            {colors.length > 0 && (
              <fieldset className="product-options">
                <legend>Couleur</legend>
                <div className="color-options">
                  {colors.map((color) => (
                    <button key={color.id} type="button"
                      className={`color-option ${selectedColorId === color.id ? 'selected' : ''}`}
                      style={{ backgroundColor: color.hex_code || undefined }}
                      disabled={!variants.some(({ color: itemColor, size, stock }) => (
                        itemColor?.id === color.id && stock > 0
                        && (selectedSizeId == null || (size?.id ?? null) === selectedSizeId)
                      ))}
                      aria-label={color.name} aria-pressed={selectedColorId === color.id}
                      onClick={() => selectColor(color.id)}>{!color.hex_code && color.name}</button>
                  ))}
                </div>
              </fieldset>
            )}
            {sizes.length > 0 && (
              <fieldset className="product-options">
                <legend>Taille</legend>
                <div className="size-options">
                  {sizes.map((size) => {
                    const available = variants.some(({ color, size: itemSize, stock }) => (
                      (selectedColorId == null || (color?.id ?? null) === selectedColorId)
                      && itemSize?.id === size.id && stock > 0
                    ));
                    return <button key={size.id} type="button" className={`size-option ${selectedSizeId === size.id ? 'selected' : ''}`}
                      disabled={!available} aria-pressed={selectedSizeId === size.id}
                      onClick={() => { setSelectedSizeId(size.id); setQuantity(1); }}>{size.name}</button>;
                  })}
                </div>
              </fieldset>
            )}
            <label className="quantity-selector">Quantité
              <input type="number" min="1" max={selectedVariant?.stock || 1} value={quantity}
                step="1"
                onChange={(event) => {
                  if (!/^\d+$/.test(event.target.value)) return;
                  setQuantity(Math.max(1, Math.min(
                    Number(event.target.value), selectedVariant?.stock || 1,
                  )));
                }} />
            </label>
            <p className="stock-info" role="status">
              {selectedVariant?.stock > 0
                ? `${selectedVariant.stock} en stock${selectedVariant.sku ? ` · SKU ${selectedVariant.sku}` : ''}`
                : 'Choisissez les options disponibles avant l’ajout'}
            </p>
            {error && <p className="product-action-error" role="alert">{error}</p>}
            <AddToCartButton disabled={!selectedVariant || selectedVariant.stock < 1 || adding} onClick={handleAdd}>
              {adding ? 'Ajout…' : 'Ajouter au panier'}
            </AddToCartButton>
          </div>
        </div>
        {related.length > 0 && (
          <section className="similar-products">
            <h2>Vous aimerez aussi</h2>
            <ProductGrid products={related} columns={4} />
          </section>
        )}
      </div>
    </main>
  );
};

export default Product;
