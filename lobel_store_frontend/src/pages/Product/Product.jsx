import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Heart, Minus, Plus } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { getProductById, getProducts } from '../../api/products';
import ProductGallery from '../../components/product/ProductGallery';
import ProductGrid from '../../components/product/ProductGrid';
import AddToCartButton from '../../components/product/AddToCartButton';
import { normalizeApiError } from '../../utils/apiErrors';
import { useCart } from '../../cart/cartState';
import { initialVariantSelection } from '../../cart/variantModel';
import './Product.css';

const MotionDiv = motion.div;

const Product = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const reducedMotion = useReducedMotion();
  const { addItem } = useCart();
  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [selectedColorId, setSelectedColorId] = useState(null);
  const [selectedSizeId, setSelectedSizeId] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setProduct(null);
    setIsFavorite(false);
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
    ({ color, size }) => (color?.id ?? null) === selectedColorId
      && (size?.id ?? null) === selectedSizeId,
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

  if (loading) {
    return <main className="product-page"><div className="product-loading">Chargement…</div></main>;
  }
  if (error && !product) {
    return (
      <main className="product-page">
        <div className="product-error" role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => navigate('/shop')}>Retour à la boutique</button>
        </div>
      </main>
    );
  }
  if (!product) return null;

  const price = Number(selectedVariant?.price ?? product.price);
  const maxQuantity = selectedVariant?.stock || 1;
  const totalPrice = price * quantity;
  const quantityControls = (
    <div className="product-quantity" aria-label="Sélectionner la quantité">
      <button type="button" aria-label="Diminuer la quantité" disabled={quantity <= 1}
        onClick={() => setQuantity((value) => Math.max(1, value - 1))}>
        <Minus aria-hidden="true" />
      </button>
      <label>
        <span className="sr-only">Quantité</span>
        <input type="number" min="1" max={maxQuantity} value={quantity} step="1"
          onChange={(event) => {
            if (!/^\d+$/.test(event.target.value)) return;
            setQuantity(Math.max(1, Math.min(Number(event.target.value), maxQuantity)));
          }} />
      </label>
      <button type="button" aria-label="Augmenter la quantité"
        disabled={!selectedVariant || quantity >= maxQuantity}
        onClick={() => setQuantity((value) => Math.min(maxQuantity, value + 1))}>
        <Plus aria-hidden="true" />
      </button>
    </div>
  );

  return (
    <main className="product-page">
      <div className="product-container">
        <MotionDiv className="product-main"
          initial={reducedMotion ? false : { opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reducedMotion ? 0 : 0.45, ease: [0.2, 0, 0, 1] }}>
          <div className="product-gallery-section">
            <button type="button" className="product-floating-action product-back"
              aria-label="Retour à la boutique" onClick={() => navigate('/shop')}>
              <ArrowLeft aria-hidden="true" />
            </button>
            <button type="button"
              className={`product-floating-action product-favorite${isFavorite ? ' is-active' : ''}`}
              aria-label={isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris'}
              aria-pressed={isFavorite} onClick={() => setIsFavorite((value) => !value)}>
              <Heart aria-hidden="true" fill={isFavorite ? 'currentColor' : 'none'} />
            </button>
            <ProductGallery media={product.media_files} productName={product.name}
              controls={quantityControls} />
          </div>

          <section className="product-info-section" aria-labelledby="product-title">
            {product.category?.name && <p className="product-category">{product.category.name}</p>}
            <h1 className="product-title" id="product-title">{product.name}</h1>
            <p className="product-description">{product.description}</p>
            <div className="product-variants-block">
              {colors.length > 0 && (
                <fieldset className="product-options">
                  <legend>Couleurs disponibles</legend>
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
                  <legend>Tailles disponibles</legend>
                  <div className="size-options">
                    {sizes.map((size) => {
                      const available = variants.some(({ color, size: itemSize, stock }) => (
                        (selectedColorId == null || (color?.id ?? null) === selectedColorId)
                        && itemSize?.id === size.id && stock > 0
                      ));
                      return (
                        <button key={size.id} type="button"
                          className={`size-option ${selectedSizeId === size.id ? 'selected' : ''}`}
                          disabled={!available} aria-pressed={selectedSizeId === size.id}
                          onClick={() => { setSelectedSizeId(size.id); setQuantity(1); }}>
                          {size.name}
                        </button>
                      );
                    })}
                  </div>
                </fieldset>
              )}
            </div>
            <p className="stock-info" role="status">
              {selectedVariant?.stock > 0
                ? `${selectedVariant.stock} en stock${selectedVariant.sku ? ` · SKU ${selectedVariant.sku}` : ''}`
                : 'Choisissez les options disponibles avant l’ajout'}
            </p>
            {error && <p className="product-action-error" role="alert">{error}</p>}
            <div className="product-desktop-quantity">{quantityControls}</div>
          </section>
        </MotionDiv>

        <div className="product-purchase-bar">
          <div className="product-total">
            <span>Prix total</span>
            <strong>{totalPrice.toLocaleString('fr-FR')} FCFA</strong>
          </div>
          <AddToCartButton disabled={!selectedVariant || selectedVariant.stock < 1 || adding}
            onClick={handleAdd}>
            {adding ? 'Ajout…' : 'Ajouter au panier'}
          </AddToCartButton>
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
