import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProductById, getProducts } from '../../api/products';
import { addOrderItem, fetchCart } from '../../api/cart';
import { useAuth } from '../../context/AuthContext';
import ProductGallery from '../../components/product/ProductGallery';
import ColorSelector from '../../components/product/ColorSelector';
import SizeSelector from '../../components/product/SizeSelector';
import AddToCartButton from '../../components/product/AddToCartButton';
import ProductGrid from '../../components/product/ProductGrid';
import './Product.css';

const Product = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, requireAuth } = useAuth();
  
  const [product, setProduct] = useState(null);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // États pour les variantes
  const [selectedColor, setSelectedColor] = useState(null);
  const [selectedSize, setSelectedSize] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [isAddingToCart, setIsAddingToCart] = useState(false);
  
  // États dérivés pour les options disponibles
  const [availableColors, setAvailableColors] = useState([]);
  const [availableSizes, setAvailableSizes] = useState([]);
  const [currentStock, setCurrentStock] = useState(0);

  useEffect(() => {
    if (id) {
      fetchProduct();
      fetchSimilarProducts();
    }
  }, [id]);

  const fetchProduct = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getProductById(id);
      const productData = response.data || response;
      
      // Mock data moderne pour développement
      if (!productData || Object.keys(productData).length === 0) {
        const mockProduct = {
          id: id,
          name: 'Robe élégante fleurie',
          price: 25000,
          description: 'Une magnifique robe fleurie conçue avec des matériaux de haute qualité. Parfaite pour les occasions spéciales ou pour une élégance quotidienne. Coupe ajustée qui met en valeur votre silhouette tout en offrant un confort optimal.',
          category: 'Robes',
          stock: 15,
          // Nouveau format de variantes avec hex_code
          variants: [
            { color: { id: 1, name: 'Rose Poudré', hex_code: '#FFB6C1' }, size: { id: 1, name: 'XS' }, stock: 3 },
            { color: { id: 1, name: 'Rose Poudré', hex_code: '#FFB6C1' }, size: { id: 2, name: 'S' }, stock: 5 },
            { color: { id: 1, name: 'Rose Poudré', hex_code: '#FFB6C1' }, size: { id: 3, name: 'M' }, stock: 4 },
            { color: { id: 1, name: 'Rose Poudré', hex_code: '#FFB6C1' }, size: { id: 4, name: 'L' }, stock: 2 },
            { color: { id: 1, name: 'Rose Poudré', hex_code: '#FFB6C1' }, size: { id: 5, name: 'XL' }, stock: 1 },
            { color: { id: 2, name: 'Beige Doux', hex_code: '#F5F5DC' }, size: { id: 1, name: 'XS' }, stock: 2 },
            { color: { id: 2, name: 'Beige Doux', hex_code: '#F5F5DC' }, size: { id: 2, name: 'S' }, stock: 6 },
            { color: { id: 2, name: 'Beige Doux', hex_code: '#F5F5DC' }, size: { id: 3, name: 'M' }, stock: 4 },
            { color: { id: 2, name: 'Beige Doux', hex_code: '#F5F5DC' }, size: { id: 4, name: 'L' }, stock: 3 },
            { color: { id: 2, name: 'Beige Doux', hex_code: '#F5F5DC' }, size: { id: 5, name: 'XL' }, stock: 0 },
            { color: { id: 3, name: 'Bleu Ciel', hex_code: '#87CEEB' }, size: { id: 1, name: 'XS' }, stock: 1 },
            { color: { id: 3, name: 'Bleu Ciel', hex_code: '#87CEEB' }, size: { id: 2, name: 'S' }, stock: 3 },
            { color: { id: 3, name: 'Bleu Ciel', hex_code: '#87CEEB' }, size: { id: 3, name: 'M' }, stock: 2 },
            { color: { id: 3, name: 'Bleu Ciel', hex_code: '#87CEEB' }, size: { id: 4, name: 'L' }, stock: 0 },
            { color: { id: 3, name: 'Bleu Ciel', hex_code: '#87CEEB' }, size: { id: 5, name: 'XL' }, stock: 1 }
          ],
          // Format média moderne avec images + vidéos - TEST COMPLET
          media: [
            { type: 'image', url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500"><rect width="400" height="500" fill="%23FFB6C1"/><text x="200" y="250" font-family="Georgia" font-size="20" fill="white" text-anchor="middle">Image 1 - Rose</text></svg>' },
            { type: 'image', url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500"><rect width="400" height="500" fill="%23F5F5DC"/><text x="200" y="250" font-family="Georgia" font-size="20" fill="%23333" text-anchor="middle">Image 2 - Beige</text></svg>' },
            { type: 'video', url: 'data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAs1tZGF0AAACrgYF//+q3EXpvebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE0OCByMjYwMSBhMGNkN2QzIC0gSC4yNjQvTVBFRy00IEFWQyBjb2RlYyAtIENvcHlsZWZ0IDIwMDMtMjAxNSAtIGh0dHA6Ly93d3cudmlkZW9sYW4ub3JnL3gyNjQuaHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMgZGVibG9jaz0xOjA6MCBhbmFseXNlPTB4MzoweDExMyBtZT1oZXggc3VibWU9NyBwc3k9MSBwc3lfcmQ9MS4wMDowLjAwIG1peGVkX3JlZj0xIG1lX3JhbmdlPTE2IGNocm9tYV9tZT0xIHRyZWxsaXM9MSA4eDhkY3Q9MSBjcW09MCBkZWFkem9uZT0yMSwxMSBmYXN0X3Bza2lwPTEgY2hyb21hX3FwX29mZnNldD0tMiB0aHJlYWRzPTEgbG9va2FoZWFkX3RocmVhZHM9MSBzbGljZWRfdGhyZWFkcz0wIG5yPTAgZGVjaW1hdGU9MSBpbnRlcmxhY2VkPTAgYmx1cmF5X2NvbXBhdD0wIGNvbnN0cmFpbmVkX2ludHJhPTAgYmZyYW1lcz0zIGJfcHlyYW1pZD0yIGJfYWRhcHQ9MSBiX2JpYXM9MCBkaXJlY3Q9MSB3ZWlnaHRiPTEgb3Blbl9nb3A9MCB3ZWlnaHRwPTIga2V5aW50PTI1MCBrZXlpbnRfbWluPTEwIHNjZW5lY3V0PTQwIGludHJhX3JlZnJlc2g9MCByY19sb29rYWhlYWQ9NDAgcmM9Y3JmIG1idHJlZT0xIGNyZj0yMy4wIHFjb21wPTAuNjAgcXBtaW49MCBxcG1heD02OSBxcHN' },
            { type: 'image', url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500"><rect width="400" height="500" fill="%23DAA520"/><text x="200" y="250" font-family="Georgia" font-size="20" fill="white" text-anchor="middle">Image 3 - Or</text></svg>' },
            { type: 'video', url: 'data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAs1tZGF0AAACrgYF//+q3EXpvebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE0OCByMjYwMSBhMGNkN2QzIC0gSC4yNjQvTVBFRy00IEFWQyBjb2RlYyAtIENvcHlsZWZ0IDIwMDMtMjAxNSAtIGh0dHA6Ly93d3cudmlkZW9sYW4ub3JnL3gyNjQuaHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMgZGVibG9jaz0xOjA6MCBhbmFseXNlPTB4MzoweDExMyBtZT1oZXggc3VibWU9NyBwc3k9MSBwc3lfcmQ9MS4wMDowLjAwIG1peGVkX3JlZj0xIG1lX3JhbmdlPTE2IGNocm9tYV9tZT0xIHRyZWxsaXM9MSA4eDhkY3Q9MSBjcW09MCBkZWFkem9uZT0yMSwxMSBmYXN0X3Bza2lwPTEgY2hyb21hX3FwX29mZnNldD0tMiB0aHJlYWRzPTEgbG9va2FoZWFkX3RocmVhZHM9MSBzbGljZWRfdGhyZWFkcz0wIG5yPTAgZGVjaW1hdGU9MSBpbnRlcmxhY2VkPTAgYmx1cmF5X2NvbXBhdD0wIGNvbnN0cmFpbmVkX2ludHJhPTAgYmZyYW1lcz0zIGJfcHlyYW1pZD0yIGJfYWRhcHQ9MSBiX2JpYXM9MCBkaXJlY3Q9MSB3ZWlnaHRiPTEgb3Blbl9nb3A9MCB3ZWlnaHRwPTIga2V5aW50PTI1MCBrZXlpbnRfbWluPTEwIHNjZW5lY3V0PTQwIGludHJhX3JlZnJlc2g9MCByY19sb29rYWhlYWQ9NDAgcmM9Y3JmIG1idHJlZT0xIGNyZj0yMy4wIHFjb21wPTAuNjAgcXBtaW49MCBxcG1heD02OSBxcHN' },
            { type: 'image', url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500"><rect width="400" height="500" fill="%2387CEEB"/><text x="200" y="250" font-family="Georgia" font-size="20" fill="white" text-anchor="middle">Image 4 - Bleu</text></svg>' }
          ]
        };
        setProduct(mockProduct);
        processVariants(mockProduct);
      } else {
        setProduct(productData);
        processVariants(productData);
      }
    } catch (err) {
      console.error('Error fetching product:', err);
      setError('Produit non trouvé');
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour traiter les variantes et extraire les options disponibles
  const processVariants = (productData) => {
    if (productData.variants && productData.variants.length > 0) {
      // Extraire les couleurs uniques
      const colors = [...new Map(productData.variants.map(v => [v.color.id, v.color])).values()];
      setAvailableColors(colors);
      
      // Extraire les tailles uniques
      const sizes = [...new Map(productData.variants.map(v => [v.size.id, v.size])).values()];
      setAvailableSizes(sizes);
      
      // Sélectionner la première couleur et taille disponibles avec du stock
      const firstAvailableVariant = productData.variants.find(v => v.stock > 0);
      if (firstAvailableVariant) {
        setSelectedColor(firstAvailableVariant.color);
        setSelectedSize(firstAvailableVariant.size);
        setCurrentStock(firstAvailableVariant.stock);
      }
    } else {
      // Fallback pour l'ancien format (compatibilité)
      if (productData.colors && productData.colors.length > 0) {
        const colors = productData.colors.map((c, index) => ({
          id: index + 1,
          name: typeof c === 'string' ? c : c.name
        }));
        setAvailableColors(colors);
        setSelectedColor(colors[0]);
      }
      
      if (productData.sizes && productData.sizes.length > 0) {
        const sizes = productData.sizes.map((s, index) => ({
          id: index + 1,
          name: typeof s === 'string' ? s : s.name
        }));
        setAvailableSizes(sizes);
        setSelectedSize(sizes[0]);
      }
      
      setCurrentStock(productData.stock || 0);
    }
  };

  // Mettre à jour le stock quand la sélection change
  useEffect(() => {
    if (product && product.variants && selectedColor && selectedSize) {
      const variant = product.variants.find(v => 
        v.color.id === selectedColor.id && v.size.id === selectedSize.id
      );
      setCurrentStock(variant ? variant.stock : 0);
    }
  }, [selectedColor, selectedSize, product]);

  // Fonctions utilitaires pour vérifier la disponibilité
  const isColorAvailable = (color) => {
    if (!product.variants) return true;
    return product.variants.some(v => v.color.id === color.id && v.stock > 0);
  };

  const isSizeAvailable = (size) => {
    if (!product.variants) return true;
    return product.variants.some(v => v.size.id === size.id && v.stock > 0);
  };

  const fetchSimilarProducts = async () => {
    try {
      const response = await getProducts();
      const allProducts = response.data || response;
      
      // Mock data si nécessaire
      if (!allProducts || allProducts.length === 0) {
        const mockSimilar = [
          {
            id: 2,
            name: 'Robe en soie',
            price: 35000,
            image: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400"><rect width="300" height="400" fill="%23DAA520"/><text x="150" y="200" font-family="Georgia" font-size="16" fill="white" text-anchor="middle">Robe Soie</text></svg>',
            category: 'Robes'
          },
          {
            id: 3,
            name: 'Robe d\'été',
            price: 18000,
            image: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400"><rect width="300" height="400" fill="%23F5F5DC"/><text x="150" y="200" font-family="Georgia" font-size="16" fill="%23333" text-anchor="middle">Robe Été</text></svg>',
            category: 'Robes'
          },
          {
            id: 4,
            name: 'Robe cocktail',
            price: 42000,
            image: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400"><rect width="300" height="400" fill="%23FF91A4"/><text x="150" y="200" font-family="Georgia" font-size="16" fill="white" text-anchor="middle">Robe Cocktail</text></svg>',
            category: 'Robes'
          }
        ];
        setSimilarProducts(mockSimilar);
      } else {
        // Filtrer les produits similaires (même catégorie, exclure le produit actuel)
        const similar = allProducts
          .filter(p => p.id !== parseInt(id) && p.category === product?.category)
          .slice(0, 4);
        setSimilarProducts(similar);
      }
    } catch (err) {
      console.error('Error fetching similar products:', err);
      setSimilarProducts([]);
    }
  };

  const handleAddToCart = async () => {
    // Protection du panier avec hook centralisé
    if (!requireAuth()) {
      return; // Redirection automatique gérée par useRequireAuth
    }

    // Vérifier si les variantes sont sélectionnées
    if (!selectedColor || !selectedSize) {
      alert('Veuillez sélectionner une couleur et une taille');
      return;
    }

    // Vérifier le stock disponible
    if (currentStock < quantity) {
      alert(`Stock insuffisant. Seulement ${currentStock} article(s) disponible(s).`);
      return;
    }

    setIsAddingToCart(true);
    
    try {
      // Préparer les données pour le panier avec le nouveau format
      const cartItem = {
        product_id: product.id,
        color_id: selectedColor.id,
        size_id: selectedSize.id,
        quantity: quantity,
        // Informations additionnelles pour l'affichage
        name: product.name,
        price: product.price,
        image: product.media?.find(m => m.type === 'image')?.url || product.image,
        color_name: selectedColor.name,
        size_name: selectedSize.name
      };

      try {
        console.log('Sending to API:', cartItem);
        
        const response = await addOrderItem({
          product_id: cartItem.product_id,
          quantity: cartItem.quantity,
        });
        
        console.log('API response:', response);
        await fetchCart();
        
        alert('Produit ajouté au panier avec succès');
        
      } catch (error) {
        console.error('Erreur ajout panier:', error);
        console.error('Response data:', error.response?.data);
        console.error('Response status:', error.response?.status);
        alert("Erreur lors de l'ajout au panier");
      }
      
    } catch (err) {
      console.error('Error adding to cart:', err);
      alert('Erreur lors de l\'ajout au panier');
    } finally {
      setIsAddingToCart(false);
    }
  };

  const handleBuyNow = async () => {
    // Protection du checkout avec hook centralisé
    if (!requireAuth()) {
      return; // Redirection automatique gérée par useRequireAuth
    }
    
    await handleAddToCart();
    navigate('/checkout');
  };

  const handleProductClick = (clickedProduct) => {
    navigate(`/product/${clickedProduct.id}`);
  };

  if (loading) {
    return (
      <div className="product-loading">
        <div className="loading-container">
          <div className="loading-skeleton">
            <div className="skeleton-gallery"></div>
            <div className="skeleton-info"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="product-error">
        <div className="error-container">
          <h2>Produit non trouvé</h2>
          <p>Le produit que vous recherchez n'existe pas ou a été supprimé.</p>
          <button 
            className="back-to-shop-btn"
            onClick={() => navigate('/shop')}
          >
            Retour à la boutique
          </button>
        </div>
      </div>
    );
  }

  // Préparer les médias pour la galerie depuis le backend
  const media = (() => {
    try {
      // Support de media_files (backend Django) en premier
      if (product?.media_files?.length > 0) {
        return product.media_files
          .filter(m => m.file && typeof m.file === 'string')
          .map(m => ({
            type: m.media_type || 'image',
            url: m.file.startsWith('http') ? m.file : `/media${m.file}`
          }));
      }
      
      // Fallback pour media (ancien format ou mock)
      if (product?.media?.length > 0) {
        return product.media
          .filter(m => m.url && typeof m.url === 'string')
          .map(m => ({
            type: m.media_type || m.type || 'image',
            url: m.file_url || m.url
          }));
      }
      
      return [];
    } catch (error) {
      console.warn('Erreur lors du traitement des médias:', error);
      return [];
    }
  })();  

  return (
    <div className="product-page">
      <div className="container">
        <div className="product-layout">
          {/* LEFT: Galerie média */}
          <div className="product-gallery-section">
            <ProductGallery 
              media={media}
              productName={product.name}
            />
          </div>

          {/* RIGHT: Infos produit */}
          <div className="product-info-section">
            <div className="product-header">
              {product.category && (
                <span className="product-category">
                  {product.category.name || product.category}
                </span>
              )}
              <h1 className="product-name">{product.name}</h1>
              <div className="product-price">
                {product.price.toLocaleString()} FCFA
              </div>
            </div>

            <div className="product-description">
              <p>{product.description}</p>
            </div>

            {/* Variantes */}
            <div className="product-variants">
              {/* Sélecteur de couleur */}
              {availableColors.length > 0 && (
                <div className="variant-selector">
                  <label className="variant-label">Couleur</label>
                  <div className="color-options">
                    {availableColors.map((color) => (
                      <div key={color.id} className="color-swatch-wrapper">
                        <button
                          className={`color-swatch ${selectedColor?.id === color.id ? 'active' : ''}`}
                          onClick={() => setSelectedColor(color)}
                          disabled={!isColorAvailable(color)}
                          style={{ backgroundColor: color.hex_code || '#ccc' }}
                          title={color.name}
                        >
                          {selectedColor?.id === color.id && (
                            <span className="color-check">?</span>
                          )}
                        </button>
                        <div className="color-tooltip">
                          {color.name}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sélecteur de taille */}
              {availableSizes.length > 0 && (
                <div className="variant-selector">
                  <label className="variant-label">Taille</label>
                  <div className="size-options">
                    {availableSizes.map((size) => (
                      <button
                        key={size.id}
                        className={`size-option ${selectedSize?.id === size.id ? 'active' : ''}`}
                        onClick={() => setSelectedSize(size)}
                        disabled={!isSizeAvailable(size)}
                      >
                        {size.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Stock */}
            <div className="product-stock">
              {currentStock > 0 ? (
                <span className="stock-available">
                  En stock ({currentStock} disponibles)
                </span>
              ) : (
                <span className="stock-unavailable">
                  Rupture de stock
                </span>
              )}
            </div>

            {/* Actions */}
            <div className="product-actions">
              {/* Message UX pour la quantité */}
              <div className="quantity-header">
                <p className="quantity-label">Choisissez la quantité souhaitée</p>
                {selectedColor && selectedSize && (
                  <p className="stock-info">Stock disponible : {currentStock}</p>
                )}
              </div>

              {/* Cas : aucune sélection */}
              {!selectedColor || !selectedSize ? (
                <div className="quantity-disabled">
                  <div className="quantity-message">
                    Veuillez sélectionner une couleur et une taille
                  </div>
                </div>
              ) : (
                /* Cas : sélection complète */
                currentStock === 0 ? (
                  <div className="quantity-disabled">
                    <div className="quantity-message stock-error">
                      Rupture de stock pour cette combinaison
                    </div>
                  </div>
                ) : (
                  <div className="quantity-selector">
                    <button 
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      className="quantity-btn"
                      disabled={quantity <= 1}
                    >
                      -
                    </button>
                    <div className="quantity-display">
                      {quantity}
                    </div>
                    <button 
                      onClick={() => setQuantity(Math.min(currentStock, quantity + 1))}
                      className="quantity-btn"
                      disabled={quantity >= currentStock}
                    >
                      +
                    </button>
                  </div>
                )
              )}

              {/* Boutons d'action - seulement si stock disponible */}
              {(selectedColor && selectedSize && currentStock > 0) && (
                <div className="action-buttons">
                  <AddToCartButton
                    onClick={handleAddToCart}
                    disabled={isAddingToCart || currentStock === 0}
                    className={isAddingToCart ? 'loading' : ''}
                  >
                    {isAddingToCart ? 'Ajout...' : 'Ajouter au panier'}
                  </AddToCartButton>
                  
                  <AddToCartButton
                    variant="secondary"
                    onClick={handleBuyNow}
                    disabled={isAddingToCart || currentStock === 0}
                    className={isAddingToCart ? 'loading' : ''}
                  >
                    {isAddingToCart ? 'Traitement...' : 'Acheter maintenant'}
                  </AddToCartButton>
                </div>
              )}
            </div>

            {/* Informations supplémentaires */}
            <div className="product-meta">
              <div className="meta-item">
                <span className="meta-label">Référence:</span>
                <span className="meta-value">#{product.id}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Date d'ajout:</span>
                <span className="meta-value">
                  {new Date(product.date_created).toLocaleDateString('fr-FR')}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Produits similaires */}
        {similarProducts.length > 0 && (
          <div className="similar-products">
            <div className="similar-products-header">
              <h2>Produits similaires</h2>
              <p>Découvrez d'autres articles qui pourraient vous plaire</p>
            </div>
            
            <ProductGrid
              products={similarProducts}
              loading={false}
              columns={4}
              onProductClick={handleProductClick}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default Product;
