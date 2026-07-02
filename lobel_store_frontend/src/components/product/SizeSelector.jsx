import React from 'react';
import './SizeSelector.css';

const SizeSelector = ({ sizes, selectedSize, onSizeChange }) => {
  if (!sizes || sizes.length === 0) {
    return null;
  }

  const handleSizeSelect = (size) => {
    onSizeChange(size);
  };

  // Déterminer l'ordre des tailles
  const sizeOrder = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '2XL', '3XL'];
  const numericSizes = [];
  const letterSizes = [];

  // Séparer les tailles numériques et alphabétiques
  sizes.forEach(size => {
    if (/^\d+$/.test(size)) {
      numericSizes.push(size);
    } else {
      letterSizes.push(size);
    }
  });

  // Trier les tailles alphabétiques selon l'ordre prédéfini
  const sortedLetterSizes = letterSizes.sort((a, b) => {
    const indexA = sizeOrder.indexOf(a.toUpperCase());
    const indexB = sizeOrder.indexOf(b.toUpperCase());
    return indexA - indexB;
  });

  // Trier les tailles numériques
  const sortedNumericSizes = numericSizes.sort((a, b) => parseInt(a) - parseInt(b));

  // Combiner les tailles triées
  const sortedSizes = [...sortedLetterSizes, ...sortedNumericSizes];

  return (
    <div className="size-selector">
      <div className="selector-label">
        Taille : <span className="selected-size">{selectedSize}</span>
      </div>
      <div className="size-options">
        {sortedSizes.map((size, index) => (
          <button
            key={index}
            className={`size-option ${size === selectedSize ? 'selected' : ''}`}
            onClick={() => handleSizeSelect(size)}
          >
            {size}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SizeSelector;
