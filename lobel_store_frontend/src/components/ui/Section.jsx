import React from 'react';
import Container from './Container';
import './Section.css';

const backgroundAliases = {
  white: 'default',
  beige: 'subtle',
  rose: 'inverse',
};

const Section = ({
  title,
  subtitle,
  children,
  className = '',
  id = '',
  background = 'white',
  align = 'center',
  containerSize = 'default',
  labelledBy,
  ...props
}) => {
  const tone = backgroundAliases[background] || background;
  const titleId = title && (labelledBy || (id ? `${id}-title` : undefined));
  const sectionClasses = `
    section
    section-${background}
    ds-section
    ${tone !== 'default' ? `ds-section--${tone}` : ''}
    ${className}
  `.trim();

  return (
    <section
      className={sectionClasses}
      id={id || undefined}
      aria-labelledby={titleId}
      {...props}
    >
      <Container size={containerSize} className="container">
        {(title || subtitle) && (
          <div className={`section-header ds-section__header ${align === 'center' ? 'ds-section__header--centered' : ''}`}>
            {title && <h2 className="section-title ds-section__title" id={titleId}>{title}</h2>}
            {subtitle && <p className="section-subtitle ds-section__subtitle">{subtitle}</p>}
          </div>
        )}
        <div className="section-content">
          {children}
        </div>
      </Container>
    </section>
  );
};

export default Section;
