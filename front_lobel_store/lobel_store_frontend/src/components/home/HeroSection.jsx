import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../ui/Button';
import './HeroSection.css';

const HeroSection = () => {
  return (
    <section className="hero-section">
      <div className="hero-background">
        <div className="hero-overlay"></div>
      </div>
      <div className="hero-content">
        <div className="hero-text">
          <span className="hero-eyebrow">Maison Lobel</span>
          <h1 className="hero-title">
            Decouvrez une elegance douce, moderne et resolument feminine
          </h1>
          <p className="hero-subtitle">
            Des silhouettes soigneusement choisies, des textures delicates et
            un vestiaire pense pour accompagner chaque instant avec grace.
          </p>
          <Link to="/shop">
            <Button variant="primary" size="large" className="hero-cta">
              Voir la boutique
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
