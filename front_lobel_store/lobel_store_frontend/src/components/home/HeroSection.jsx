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
          <h1 className="hero-title">
            Découvrez les nouvelles collections
          </h1>
          <p className="hero-subtitle">
            Élégance et style contemporain pour sublimer votre quotidien. 
            Explorez nos pièces uniques et tendances.
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
