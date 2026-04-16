import React from 'react';
import HeroSection from '../../components/home/HeroSection';
import NewProductsSection from '../../components/home/NewProductsSection';
import CollectionsSection from '../../components/home/CollectionsSection';
import ProductsSection from '../../components/home/ProductsSection';
import './Home.css';

const Home = () => {
  return (
    <div className="home">
      <HeroSection />
      <NewProductsSection />
      <CollectionsSection />
      <ProductsSection />
    </div>
  );
};

export default Home;
