import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import Container from './Container';
import './Section.css';

const MotionH2 = motion.h2;

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
  animateTitle = false,
  ...props
}) => {
  const reducedMotion = useReducedMotion();
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
            {title && (
              <MotionH2
                className="section-title ds-section__title"
                id={titleId}
                initial={animateTitle && !reducedMotion
                  ? { y: 18, letterSpacing: '0.025em' }
                  : false}
                whileInView={animateTitle
                  ? { y: 0, letterSpacing: '-0.025em' }
                  : undefined}
                viewport={{ once: true, amount: 0.7 }}
                transition={{ duration: reducedMotion ? 0 : 0.8, ease: [0.2, 0, 0, 1] }}
              >
                {title}
              </MotionH2>
            )}
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
