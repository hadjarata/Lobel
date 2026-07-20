import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion as Motion } from 'framer-motion';
import { backdropVariants, slideFromLeftVariants, springModal, springSheet } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';
import './FilterSidebar.css';

const Section = ({ name, title, expanded, toggle, children }) => (
  <div className="filter-section">
    <button
      type="button"
      className="filter-section-header"
      aria-expanded={expanded}
      aria-controls={`filter-${name}`}
      onClick={() => toggle(name)}
    >
      <span className="filter-section-title">{title}</span>
      <span aria-hidden="true" className={`chevron ${expanded ? 'open' : ''}`}>⌄</span>
    </button>
    {expanded && <div id={`filter-${name}`} className="filter-section-content">{children}</div>}
  </div>
);

const FilterSidebar = ({
  id,
  query,
  options,
  onChange,
  onClear,
  isMobile = false,
  isOpen = false,
  onClose = () => {},
}) => {
  const [expanded, setExpanded] = useState({
    collection: true, category: true, price: true, size: true, color: true, availability: true,
  });
  const overlayTransition = useMotionTransition(springModal);
  const panelTransition = useMotionTransition(springSheet);
  const toggle = (name) => setExpanded((current) => ({ ...current, [name]: !current[name] }));

  useEffect(() => {
    if (!isMobile || !isOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [isMobile, isOpen, onClose]);

  const content = (
    <>
      <div className="filter-header">
        <h3 className="filter-title">Filtres</h3>
        <div className="filter-actions">
          <button type="button" className="clear-filters-btn" onClick={onClear}>Tout effacer</button>
          {isMobile && (
            <button type="button" className="close-filters-btn" aria-label="Fermer les filtres" onClick={onClose}>×</button>
          )}
        </div>
      </div>
      <div className="filter-content">
        <Section name="collection" title="Collections" expanded={expanded.collection} toggle={toggle}>
          {options.collections.map((item) => (
            <label key={item.slug} className="filter-item">
              <input type="radio" name="collection" checked={query.collection === item.slug}
                onChange={() => onChange('collection', query.collection === item.slug ? null : item.slug)} />
              <span className="filter-label">{item.name}</span>
            </label>
          ))}
        </Section>
        <Section name="category" title="Catégories" expanded={expanded.category} toggle={toggle}>
          {options.categories.map((item) => (
            <label key={item.id} className="filter-item">
              <input type="radio" name="category" checked={query.category === item.id}
                onChange={() => onChange('category', query.category === item.id ? null : item.id)} />
              <span className="filter-label">{item.name}</span>
            </label>
          ))}
        </Section>
        <Section name="price" title="Prix" expanded={expanded.price} toggle={toggle}>
          <div className="price-fields">
            <label>Minimum
              <input type="number" min="0" inputMode="decimal" value={query.minPrice ?? ''}
                placeholder={options.price.min ?? '0'}
                onChange={(event) => onChange('minPrice', event.target.value || null)} />
            </label>
            <label>Maximum
              <input type="number" min="0" inputMode="decimal" value={query.maxPrice ?? ''}
                placeholder={options.price.max ?? ''}
                onChange={(event) => onChange('maxPrice', event.target.value || null)} />
            </label>
          </div>
        </Section>
        <Section name="size" title="Tailles" expanded={expanded.size} toggle={toggle}>
          <div className="size-grid">
            {options.sizes.map((item) => (
              <label key={item.id} className="size-item">
                <input type="radio" name="size" checked={query.size === item.id}
                  onChange={() => onChange('size', query.size === item.id ? null : item.id)} />
                <span className="size-label">{item.name}</span>
              </label>
            ))}
          </div>
        </Section>
        <Section name="color" title="Couleurs" expanded={expanded.color} toggle={toggle}>
          {options.colors.map((item) => (
            <label key={item.id} className="filter-item">
              <input type="radio" name="color" checked={query.color === item.id}
                onChange={() => onChange('color', query.color === item.id ? null : item.id)} />
              <span className="filter-label">
                {item.hex_code && <span className="color-swatch" style={{ backgroundColor: item.hex_code }} aria-hidden="true" />}
                {item.name}
              </span>
            </label>
          ))}
        </Section>
        <Section name="availability" title="Disponibilité" expanded={expanded.availability} toggle={toggle}>
          <label className="filter-item">
            <input type="checkbox" checked={query.available === true}
              onChange={() => onChange('available', query.available === true ? null : true)} />
            <span className="filter-label">En stock uniquement</span>
          </label>
        </Section>
      </div>
    </>
  );

  if (!isMobile) return <div id={id} className="filter-sidebar desktop">{content}</div>;
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <Motion.button type="button" className="filter-overlay" aria-label="Fermer les filtres"
            onClick={onClose} variants={backdropVariants} initial="initial" animate="animate" exit="exit"
            transition={overlayTransition} />
          <Motion.div id={id} role="dialog" aria-modal="true" aria-label="Filtres du catalogue"
            className="filter-sidebar mobile open" variants={slideFromLeftVariants}
            initial="initial" animate="animate" exit="exit" transition={panelTransition}>
            {content}
          </Motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default FilterSidebar;
