import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../ui/Button';
import './ProductInfo.css';

const ProductInfo = ({ 
  product = {},
  onAddToCart = () => {},
  onBuyNow = () => {}
}) => {
  const navigate = useNavigate();
  const [selectedSize, setSelectedSize] = useState('');
  const [selectedColor, setSelectedColor] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [activeTab, setActiveTab] = useState('description');

  const {
    name = '',
    price = 0,
    description = '',
    category = '',
    stock = 0,
    sizes = [],
    colors = [],
    images = []
  } = product;

  const handleSizeChange = (size) => {
    setSelectedSize(selectedSize === size ? '' : size);
  };

  const handleColorChange = (color) => {
    setSelectedColor(selectedColor === color ? '' : color);
  };

  const handleQuantityChange = (newQuantity) => {
    if (newQuantity >= 1 && newQuantity <= stock) {
      setQuantity(newQuantity);
    }
  };

  const handleAddToCart = () => {
    // Vérifier si l'utilisateur est connecté (simulation)
    const isLoggedIn = localStorage.getItem('token'); // À remplacer par vrai contexte auth
    
    if (!isLoggedIn) {
      navigate('/login');
      return;
    }

    if (!selectedSize || !selectedColor) {
      alert('Veuillez sélectionner une taille et une couleur');
      return;
    }

    onAddToCart({
      ...product,
      selectedSize,
      selectedColor,
      quantity
    });
  };

  const handleBuyNow = () => {
    // Vérifier si l'utilisateur est connecté (simulation)
    const isLoggedIn = localStorage.getItem('token'); // À remplacer par vrai contexte auth
    
    if (!isLoggedIn) {
      navigate('/login');
      return;
    }

    if (!selectedSize || !selectedColor) {
      alert('Veuillez sélectionner une taille et une couleur');
      return;
    }

    onBuyNow({
      ...product,
      selectedSize,
      selectedColor,
      quantity
    });
  };

  const isInStock = stock > 0;
  const canAddToCart = isInStock && selectedSize && selectedColor;

  return (
    <div className="product-info">
      {/* Header */}
      <div className="product-header">
        {category && <span className="product-category">{category}</span>}
        <h1 className="product-name">{name}</h1>
        <div className="product-price-row">
          <span className="product-price">{price.toLocaleString()} FCFA</span>
          {!isInStock && (
            <span className="stock-status out-of-stock">Rupture de stock</span>
          )}
        </div>
      </div>

      {/* Description */}
      <div className="product-description">
        <p>{description}</p>
      </div>

      {/* Options */}
      <div className="product-options">
        {/* Tailles */}
        {sizes.length > 0 && (
          <div className="option-group">
            <label className="option-label">Taille</label>
            <div className="size-options">
              {sizes.map((size) => (
                <button
                  key={size}
                  className={`size-option ${selectedSize === size ? 'selected' : ''}`}
                  onClick={() => handleSizeChange(size)}
                  disabled={!isInStock}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Couleurs */}
        {colors.length > 0 && (
          <div className="option-group">
            <label className="option-label">Couleur</label>
            <div className="color-options">
              {colors.map((color) => (
                <button
                  key={color.value}
                  className={`color-option ${selectedColor === color.value ? 'selected' : ''}`}
                  onClick={() => handleColorChange(color.value)}
                  disabled={!isInStock}
                  title={color.name}
                >
                  <span 
                    className="color-swatch"
                    style={{ backgroundColor: color.value }}
                  ></span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Quantité */}
        {isInStock && (
          <div className="option-group">
            <label className="option-label">Quantité</label>
            <div className="quantity-selector">
              <button 
                className="quantity-btn"
                onClick={() => handleQuantityChange(quantity - 1)}
                disabled={quantity <= 1}
              >
                -
              </button>
              <span className="quantity-value">{quantity}</span>
              <button 
                className="quantity-btn"
                onClick={() => handleQuantityChange(quantity + 1)}
                disabled={quantity >= stock}
              >
                +
              </button>
            </div>
            <span className="stock-info">{stock} articles disponibles</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="product-actions">
        <Button
          variant="primary"
          size="large"
          className="add-to-cart-btn"
          onClick={handleAddToCart}
          disabled={!canAddToCart}
        >
          Ajouter au panier
        </Button>
        
        <Button
          variant="secondary"
          size="large"
          className="buy-now-btn"
          onClick={handleBuyNow}
          disabled={!canAddToCart}
        >
          Acheter maintenant
        </Button>
      </div>

      {/* Informations supplémentaires */}
      <div className="product-details">
        <div className="details-tabs">
          <button
            className={`tab-btn ${activeTab === 'description' ? 'active' : ''}`}
            onClick={() => setActiveTab('description')}
          >
            Description
          </button>
          <button
            className={`tab-btn ${activeTab === 'shipping' ? 'active' : ''}`}
            onClick={() => setActiveTab('shipping')}
          >
            Livraison
          </button>
          <button
            className={`tab-btn ${activeTab === 'returns' ? 'active' : ''}`}
            onClick={() => setActiveTab('returns')}
          >
            Retours
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'description' && (
            <div className="tab-pane">
              <p>{description}</p>
              <ul className="product-features">
                <li>Fabrication de haute qualité</li>
                <li>Matières premières premium</li>
                <li>Design exclusif Lobel Store</li>
                <li>Lavage facile et entretien simple</li>
              </ul>
            </div>
          )}

          {activeTab === 'shipping' && (
            <div className="tab-pane">
              <h4>Livraison</h4>
              <ul>
                <li>Livraison standard : 3-5 jours ouvrables</li>
                <li>Livraison express : 1-2 jours ouvrables</li>
                <li>Livraison gratuite à partir de 50 000 FCFA</li>
                <li>Suivi de commande en temps réel</li>
              </ul>
            </div>
          )}

          {activeTab === 'returns' && (
            <div className="tab-pane">
              <h4>Retours et échanges</h4>
              <ul>
                <li>Retour gratuit sous 14 jours</li>
                <li>Article non porté avec étiquettes intactes</li>
                <li>Remboursement ou échange possible</li>
                <li>Service client disponible 7j/7</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductInfo;
