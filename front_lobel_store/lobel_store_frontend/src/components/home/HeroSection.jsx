import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../ui/Button';
import './HeroSection.css';

const HeroSection = () => {
  return (
    <section className="hero-section">
      <div className="hero-content">
        <div className="hero-text">
          <span className="hero-eyebrow">Maison Lobel</span>
          <h1 className="hero-title">
            Découvrez une élégance douce, moderne et résolument féminine
          </h1>
          <p className="hero-subtitle">
            Des silhouettes soigneusement choisies, des textures délicates et
            un vestiaire pensé pour accompagner chaque instant avec grâce.
          </p>
          <Link to="/shop">
            <button className="hero-cta">
              Voir la boutique
            </button>
          </Link>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
