import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProductById, getProducts } from '../../services/productService';
import { useAuth } from '../../context/AuthContext';
import ProductGallery from '../../components/product/ProductGallery';
import ColorSelector from '../../components/product/ColorSelector';
import SizeSelector from '../../components/product/SizeSelector';
import AddToCartButton from '../../components/product/AddToCartButton';
import ProductGrid from '../../components/products/ProductGrid';
import './Product.css';

const Product = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { requireAuth, isAuthenticated } = useAuth();
  
  const [product, setProduct] = useState(null);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // États pour les variantes
  const [selectedColor, setSelectedColor] = useState('');
  const [selectedSize, setSelectedSize] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [isAddingToCart, setIsAddingToCart] = useState(false);

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
          sizes: ['XS', 'S', 'M', 'L', 'XL'],
          colors: [
            { name: 'Rose', value: '#FFB6C1' },
            { name: 'Beige', value: '#F5F5DC' },
            { name: 'Bleu', value: '#4A90E2' }
          ],
          // Format média moderne avec images + vidéos
          media: [
            { type: 'image', url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500"><rect width="400" height="500" fill="%23FFB6C1"/><text x="200" y="250" font-family="Georgia" font-size="20" fill="white" text-anchor="middle">Robe Fleurie</text></svg>' },
            { type: 'image', url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500"><rect width="400" height="500" fill="%23F5F5DC"/><text x="200" y="250" font-family="Georgia" font-size="20" fill="%23333" text-anchor="middle">Vue Dos</text></svg>' },
            { type: 'video', url: 'data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAs1tZGF0AAACrgYF//+q3EXpvebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE0OCByMjYwMSBhMGNkN2QzIC0gSC4yNjQvTVBFRy00IEFWQyBjb2RlYyAtIENvcHlsZWZ0IDIwMDMtMjAxNSAtIGh0dHA6Ly93d3cudmlkZW9sYW4ub3JnL3gyNjQuaHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMgZGVibG9jaz0xOjA6MCBhbmFseXNlPTB4MzoweDExMyBtZT1oZXggc3VibWU9NyBwc3k9MSBwc3lfcmQ9MS4wMDowLjAwIG1peGVkX3JlZj0xIG1lX3JhbmdlPTE2IGNocm9tYV9tZT0xIHRyZWxsaXM9MSA4eDhkY3Q9MSBjcW09MCBkZWFkem9uZT0yMSwxMSBmYXN0X3Bza2lwPTEgY2hyb21hX3FwX29mZnNldD0tMiB0aHJlYWRzPTEgbG9va2FoZWFkX3RocmVhZHM9MSBzbGljZWRfdGhyZWFkcz0wIG5yPTAgZGVjaW1hdGU9MSBpbnRlcmxhY2VkPTAgYmx1cmF5X2NvbXBhdD0wIGNvbnN0cmFpbmVkX2ludHJhPTAgYmZyYW1lcz0zIGJfcHlyYW1pZD0yIGJfYWRhcHQ9MSBiX2JpYXM9MCBkaXJlY3Q9MSB3ZWlnaHRiPTEgb3Blbl9nb3A9MCB3ZWlnaHRwPTIga2V5aW50PTI1MCBrZXlpbnRfbWluPTEwIHNjZW5lY3V0PTQwIGludHJhX3JlZnJlc2g9MCByY19sb29rYWhlYWQ9NDAgcmM9Y3JmIG1idHJlZT0xIGNyZj0yMy4wIHFjb21wPTAuNjAgcXBtaW49MCBxcG1heD02OSBxcHN0ZXA9NCBpcF9yYXRpbz0xLjQwIGFxPTE6MS4wMACAAAAAD2WIhAA3//728P4FNjuZQQAAAu5tb292AAAAbG12aGQAAAAAAAAAAAAAAAAAAAPoAAAAZAABAAABAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAACGHRyYWsAAABcdGtoZAAAAAMAAAAAAAAAAAAAAAEAAAAAAAAAZAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAEAAAAAAAgAAAAIAAAAAACRlZHRzAAAAHGVsc3QAAAAAAAAAAQAAAGQAAAAAAAEAAAAAAZBtZGlhAAAAIG1kaGQAAAAAAAAAAAAAAAAAACgAAAAEAFXEAAAAAAAtaGRscgAAAAAAAAAAdmlkZQAAAAAAAAAAAAAAAFZpZGVvSGFuZGxlcgAAAAE7bWluZgAAABR2bWhkAAAAAQAAAAAAAAAAAAAAJGRpbmYAAAAcZHJlZgAAAAAAAAABAAAADHVybCAAAAABAAAA+3N0YmwAAACXc3RzZAAAAAAAAAABAAAAh2F2YzEAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAgACAEgAAABIAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY//8AAAAxYXZjQwFNQAr/4QAYZ01ACuiPyLZYAQAEaO+G8gAAABhzdHRzAAAAAAAAAAEAAAABAAAABAAAABxzdHNjAAAAAAAAAAEAAAABAAAAAQAAAAEAAAAUc3RzegAAAAAAAAAAAAAAAQAAABRzdGNvAAAAAAAAAAEAAAAsAAAAYnVkdGEAAABabWV0YQAAAAAAAAAhaGRscgAAAAAAAAAAbWRpcmFwcGwAAAAAAAAAAAAAAAAraWxzdAAAACOpdG9vAAAAG2RhdGEAAAABAAAAAExhdmY1Ni4xNS4xMDI=' },
            { type: 'image', url: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500"><rect width="400" height="500" fill="%23DAA520"/><text x="200" y="250" font-family="Georgia" font-size="20" fill="white" text-anchor="middle">Détail</text></svg>' }
          ]
        };
        setProduct(mockProduct);
        
        // Sélectionner la première couleur et taille par défaut
        if (mockProduct.colors && mockProduct.colors.length > 0) {
          setSelectedColor(mockProduct.colors[0].name);
        }
        if (mockProduct.sizes && mockProduct.sizes.length > 0) {
          setSelectedSize(mockProduct.sizes[0]);
        }
      } else {
        setProduct(productData);
        
        // Gérer les données réelles de l'API
        if (productData.colors && productData.colors.length > 0) {
          setSelectedColor(productData.colors[0].name || productData.colors[0]);
        }
        if (productData.sizes && productData.sizes.length > 0) {
          setSelectedSize(productData.sizes[0]);
        }
      }
    } catch (err) {
      console.error('Error fetching product:', err);
      setError('Produit non trouvé');
    } finally {
      setLoading(false);
    }
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
    // Protection du panier - vérifier l'authentification
    if (!isAuthenticated) {
      requireAuth();
      return;
    }

    // Vérifier si les variantes sont sélectionnées
    if (!selectedColor || !selectedSize) {
      alert('Veuillez sélectionner une couleur et une taille');
      return;
    }

    setIsAddingToCart(true);
    
    try {
      // Préparer les données pour le panier
      const cartItem = {
        productId: product.id,
        name: product.name,
        price: product.price,
        image: product.media?.find(m => m.type === 'image')?.url || product.image,
        color: selectedColor,
        size: selectedSize,
        quantity: quantity
      };

      // TODO: Appeler l'API du panier quand elle sera prête
      console.log('Adding to cart:', cartItem);
      
      // Simulation d'ajout au panier
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Afficher un message de succès
      alert('Produit ajouté au panier avec succès!');
      
    } catch (err) {
      console.error('Error adding to cart:', err);
      alert('Erreur lors de l\'ajout au panier');
    } finally {
      setIsAddingToCart(false);
    }
  };

  const handleBuyNow = async () => {
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
  const media = product.media && product.media.length > 0 
    ? product.media.map(m => ({
        type: m.media_type,
        url: m.file_url  // Utiliser l'URL complète fournie par l'API
      }))
    : [
        { type: 'image', url: product.image },
        ...(product.video ? [{ type: 'video', url: product.video }] : [])
      ];  

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
              {product.colors && product.colors.length > 0 && (
                <ColorSelector
                  colors={product.colors}
                  selectedColor={selectedColor}
                  onColorChange={setSelectedColor}
                />
              )}

              {/* Sélecteur de taille */}
              {product.sizes && product.sizes.length > 0 && (
                <SizeSelector
                  sizes={product.sizes}
                  selectedSize={selectedSize}
                  onSizeChange={setSelectedSize}
                />
              )}
            </div>

            {/* Stock */}
            <div className="product-stock">
              {product.stock > 0 ? (
                <span className="stock-available">
                  ✓ En stock ({product.stock} disponibles)
                </span>
              ) : (
                <span className="stock-unavailable">
                  ✗ Rupture de stock
                </span>
              )}
            </div>

            {/* Actions */}
            <div className="product-actions">
              <div className="quantity-selector">
                <button 
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="quantity-btn"
                  disabled={quantity <= 1}
                >
                  -
                </button>
                <input 
                  type="number" 
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="quantity-input"
                  min="1"
                  max={product.stock}
                />
                <button 
                  onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
                  className="quantity-btn"
                  disabled={quantity >= product.stock}
                >
                  +
                </button>
              </div>

              <div className="action-buttons">
                <AddToCartButton
                  onClick={handleAddToCart}
                  disabled={isAddingToCart || product.stock === 0}
                  className={isAddingToCart ? 'loading' : ''}
                >
                  {isAddingToCart ? 'Ajout...' : 'Ajouter au panier'}
                </AddToCartButton>
                
                <AddToCartButton
                  variant="secondary"
                  onClick={handleBuyNow}
                  disabled={isAddingToCart || product.stock === 0}
                  className={isAddingToCart ? 'loading' : ''}
                >
                  {isAddingToCart ? 'Traitement...' : 'Acheter maintenant'}
                </AddToCartButton>
              </div>
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
