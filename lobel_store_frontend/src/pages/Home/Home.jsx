import React from 'react';
import HeroSection from '../../components/home/HeroSection';
import NewProductsSection from '../../components/home/NewProductsSection';
import CollectionsSection from '../../components/home/CollectionsSection';
import ProductsSection from '../../components/home/ProductsSection';
import CustomDressSection from '../../components/home/CustomDressSection';
import HomeReveal from '../../components/home/HomeReveal';
import './Home.css';

const Home = () => {
  return (
    <main className="home">
      <HeroSection />
      <HomeReveal><NewProductsSection /></HomeReveal>
      <HomeReveal><CustomDressSection /></HomeReveal>
      <HomeReveal><CollectionsSection /></HomeReveal>
      <HomeReveal><ProductsSection /></HomeReveal>
    </main>
  );
};

export default Home;
