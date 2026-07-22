import React from 'react';
import { motion as Motion, useReducedMotion } from 'framer-motion';
import { ArrowUpRight } from 'lucide-react';
import logo from '../../logo/LOBEL PROFIL 4.jpg.jpeg';

const AuthPageShell = ({ eyebrow, title, description, note, children }) => {
  const reduceMotion = useReducedMotion();
  const reveal = reduceMotion
    ? { initial: false }
    : {
        initial: { opacity: 0, y: 18 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] },
      };

  return (
    <main className="auth-entry-page">
      <Motion.aside className="auth-entry-story" {...reveal} aria-label="LobelStore">
        <div className="auth-entry-brand">
          <img src={logo} alt="LobelStore" />
          <span>Maison de style</span>
        </div>
        <div className="auth-entry-story-copy">
          <span className="auth-entry-index">L / 01</span>
          <p>{note}</p>
          <ArrowUpRight aria-hidden="true" size={24} strokeWidth={1.4} />
        </div>
      </Motion.aside>

      <section className="auth-entry-content">
        <Motion.div className="auth-entry-card" {...reveal}>
          <header className="auth-entry-header">
            <span className="auth-entry-eyebrow">{eyebrow}</span>
            <h1>{title}</h1>
            <p>{description}</p>
          </header>
          {children}
        </Motion.div>
      </section>
    </main>
  );
};

export default AuthPageShell;
