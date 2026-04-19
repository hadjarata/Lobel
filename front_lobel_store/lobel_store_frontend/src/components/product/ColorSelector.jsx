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
        Couleur : <span className="selected-color">{selectedColor}</span>
      </div>
      <div className="color-options">
        {colors.map((color, index) => {
          const colorValue = getColorValue(color);
          const colorName = getColorName(color);
          const selected = isSelected(color);
          
          return (
            <button
              key={index}
              className={`color-option ${selected ? 'selected' : ''}`}
              style={{ backgroundColor: colorValue }}
              onClick={() => handleColorSelect(color)}
              title={colorName}
              aria-label={`Couleur ${colorName}`}
            >
              {selected && (
                <div className="color-check">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default ColorSelector;
