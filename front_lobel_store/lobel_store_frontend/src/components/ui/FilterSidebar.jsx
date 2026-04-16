import React, { useState } from 'react';
import './FilterSidebar.css';

const FilterSidebar = ({ 
  filters = {}, 
  onFilterChange = () => {},
  isMobile = false,
  isOpen = false,
  onClose = () => {}
}) => {
  const [expandedSections, setExpandedSections] = useState({
    category: true,
    price: true,
    size: true,
    color: true
  });

  const categories = [
    'Robes',
    'Tops',
    'Pantalons', 
    'Jupes',
    'Accessoires'
  ];

  const priceRanges = [
    { label: 'Moins de 10 000 FCFA', min: 0, max: 10000 },
    { label: '10 000 - 20 000 FCFA', min: 10000, max: 20000 },
    { label: '20 000 - 30 000 FCFA', min: 20000, max: 30000 },
    { label: 'Plus de 30 000 FCFA', min: 30000, max: Infinity }
  ];

  const sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
  const colors = [
    { name: 'Noir', value: '#000000' },
    { name: 'Blanc', value: '#FFFFFF' },
    { name: 'Rose', value: '#FFB6C1' },
    { name: 'Beige', value: '#F5F5DC' },
    { name: 'Bleu', value: '#4A90E2' },
    { name: 'Rouge', value: '#FF6B6B' }
  ];

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleCategoryChange = (category) => {
    onFilterChange('category', category);
  };

  const handlePriceChange = (range) => {
    onFilterChange('price', range);
  };

  const handleSizeChange = (size) => {
    onFilterChange('size', size);
  };

  const handleColorChange = (color) => {
    onFilterChange('color', color);
  };

  const clearFilters = () => {
    onFilterChange('clear', {});
  };

  const sidebarClasses = `
    filter-sidebar
    ${isMobile ? 'mobile' : 'desktop'}
    ${isMobile && isOpen ? 'open' : ''}
  `;

  if (isMobile && !isOpen) {
    return null;
  }

  return (
    <>
      {isMobile && (
        <div className="filter-overlay" onClick={onClose}></div>
      )}
      <div className={sidebarClasses}>
        <div className="filter-header">
          <h3 className="filter-title">Filtres</h3>
          <div className="filter-actions">
            <button className="clear-filters-btn" onClick={clearFilters}>
              Tout effacer
            </button>
            {isMobile && (
              <button className="close-filters-btn" onClick={onClose}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            )}
          </div>
        </div>

        <div className="filter-content">
          {/* Catégories */}
          <div className="filter-section">
            <div 
              className="filter-section-header"
              onClick={() => toggleSection('category')}
            >
              <h4 className="filter-section-title">Catégories</h4>
              <svg 
                className={`chevron ${expandedSections.category ? 'open' : ''}`}
                width="20" 
                height="20" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2"
              >
                <polyline points="6,9 12,15 18,9"></polyline>
              </svg>
            </div>
            {expandedSections.category && (
              <div className="filter-section-content">
                {categories.map((category) => (
                  <label key={category} className="filter-item">
                    <input
                      type="checkbox"
                      checked={filters.category === category}
                      onChange={() => handleCategoryChange(category)}
                    />
                    <span className="filter-label">{category}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Prix */}
          <div className="filter-section">
            <div 
              className="filter-section-header"
              onClick={() => toggleSection('price')}
            >
              <h4 className="filter-section-title">Prix</h4>
              <svg 
                className={`chevron ${expandedSections.price ? 'open' : ''}`}
                width="20" 
                height="20" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2"
              >
                <polyline points="6,9 12,15 18,9"></polyline>
              </svg>
            </div>
            {expandedSections.price && (
              <div className="filter-section-content">
                {priceRanges.map((range, index) => (
                  <label key={index} className="filter-item">
                    <input
                      type="radio"
                      name="price"
                      checked={filters.price?.label === range.label}
                      onChange={() => handlePriceChange(range)}
                    />
                    <span className="filter-label">{range.label}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Tailles */}
          <div className="filter-section">
            <div 
              className="filter-section-header"
              onClick={() => toggleSection('size')}
            >
              <h4 className="filter-section-title">Tailles</h4>
              <svg 
                className={`chevron ${expandedSections.size ? 'open' : ''}`}
                width="20" 
                height="20" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2"
              >
                <polyline points="6,9 12,15 18,9"></polyline>
              </svg>
            </div>
            {expandedSections.size && (
              <div className="filter-section-content">
                <div className="size-grid">
                  {sizes.map((size) => (
                    <label key={size} className="size-item">
                      <input
                        type="checkbox"
                        checked={filters.size?.includes(size)}
                        onChange={() => handleSizeChange(size)}
                      />
                      <span className="size-label">{size}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Couleurs */}
          <div className="filter-section">
            <div 
              className="filter-section-header"
              onClick={() => toggleSection('color')}
            >
              <h4 className="filter-section-title">Couleurs</h4>
              <svg 
                className={`chevron ${expandedSections.color ? 'open' : ''}`}
                width="20" 
                height="20" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2"
              >
                <polyline points="6,9 12,15 18,9"></polyline>
              </svg>
            </div>
            {expandedSections.color && (
              <div className="filter-section-content">
                <div className="color-grid">
                  {colors.map((color) => (
                    <label key={color.value} className="color-item">
                      <input
                        type="checkbox"
                        checked={filters.color?.includes(color.value)}
                        onChange={() => handleColorChange(color.value)}
                      />
                      <span 
                        className="color-swatch"
                        style={{ backgroundColor: color.value }}
                        title={color.name}
                      ></span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default FilterSidebar;
