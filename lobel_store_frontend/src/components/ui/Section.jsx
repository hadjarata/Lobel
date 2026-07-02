import React from 'react';
import './Section.css';

const Section = ({ 
  title, 
  subtitle, 
  children, 
  className = '',
  id = '',
  background = 'white' 
}) => {
  const sectionClasses = `
    section
    section-${background}
    ${className}
  `.trim();

  return (
    <section className={sectionClasses} id={id}>
      <div className="container">
        {(title || subtitle) && (
          <div className="section-header">
            {title && <h2 className="section-title">{title}</h2>}
            {subtitle && <p className="section-subtitle">{subtitle}</p>}
          </div>
        )}
        <div className="section-content">
          {children}
        </div>
      </div>
    </section>
  );
};

export default Section;
