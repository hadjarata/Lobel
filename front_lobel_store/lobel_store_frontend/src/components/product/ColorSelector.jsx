import React from 'react';
import './ColorSelector.css';

const ColorSelector = ({ colors, selectedColor, onColorChange }) => {
  if (!colors || colors.length === 0) {
    return null;
  }

  const handleColorSelect = (color) => {
    // Gérer les deux formats possibles: objet {name, value} ou string
    const colorValue = typeof color === 'object' ? color.name : color;
    onColorChange(colorValue);
  };

  const getColorValue = (color) => {
    return typeof color === 'object' ? color.value : color;
  };

  const getColorName = (color) => {
    return typeof color === 'object' ? color.name : color;
  };

  const isSelected = (color) => {
    const colorName = getColorName(color);
    return colorName === selectedColor;
  };

  return (
    <div className="color-selector">
      <div className="selector-label">
        <span>Couleur</span>
        {selectedColor && (
          <span className="selected-value">
            {selectedColor}
          </span>
        )}
      </div>
      <div className="color-options">
        {colors.map((color, index) => (
          <button
            key={index}
            className={`color-option ${isSelected(color) ? 'selected' : ''}`}
            onClick={() => handleColorSelect(color)}
            aria-label={`Couleur ${getColorName(color)}`}
            title={getColorName(color)}
            style={{
              backgroundColor: getColorValue(color)
            }}
          >
            {isSelected(color) && (
              <span className="checkmark">✓</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ColorSelector;
