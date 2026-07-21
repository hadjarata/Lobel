import { useEffect, useRef, useState } from 'react';
import { ExternalLink, MessageCircle, X } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { getCustomDressService } from '../../api/homeContent';
import {
  Badge, Button, Card, Section,
} from '../ui';
import './CustomDressSection.css';

const MotionLi = motion.li;

const CustomDressSection = () => {
  const [service, setService] = useState(null);
  const [imageFailed, setImageFailed] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const reducedMotion = useReducedMotion();
  const dialogRef = useRef(null);
  const openerRef = useRef(null);
  const continueRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    getCustomDressService({ signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted) setService(value);
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);

  const openDialog = () => {
    setDialogOpen(true);
    dialogRef.current?.showModal();
    window.requestAnimationFrame(() => continueRef.current?.focus());
  };

  const closeDialog = () => {
    setDialogOpen(false);
    dialogRef.current?.close();
    openerRef.current?.focus();
  };

  if (!service) return null;
  const whatsappUrl = `https://wa.me/${service.whatsappPhone}?text=${encodeURIComponent(service.whatsappMessage)}`;

  return (
    <Section className="custom-dress-section" aria-labelledby="custom-dress-title">
      <Card className="custom-dress-layout" padded={false}>
        <div className={`custom-dress-media${imageFailed ? ' is-fallback' : ''}`}>
          {service.imageUrl && !imageFailed && (
            <img
              src={service.imageUrl}
              alt=""
              loading="lazy"
              width="720"
              height="720"
              onError={() => setImageFailed(true)}
            />
          )}
        </div>
        <div className="custom-dress-content">
          <Badge className="custom-dress-eyebrow">Confection sur mesure</Badge>
          <h2 id="custom-dress-title">{service.title}</h2>
          <p className="custom-dress-description">{service.description}</p>
          <div className="custom-dress-details">
            {service.availabilityText && <p>{service.availabilityText}</p>}
            {service.responseTimeText && <p>{service.responseTimeText}</p>}
            {service.pricingNotice && <p className="custom-dress-pricing">{service.pricingNotice}</p>}
          </div>
          <Button ref={openerRef} className="custom-dress-button" onClick={openDialog}>
            <MessageCircle aria-hidden="true" />
            {service.buttonLabel}
          </Button>
        </div>
      </Card>
      <dialog
        ref={dialogRef}
        className="custom-dress-dialog"
        aria-labelledby="custom-dress-dialog-title"
        onCancel={(event) => {
          event.preventDefault();
          closeDialog();
        }}
        onClose={() => openerRef.current?.focus()}
      >
        <div className="custom-dress-dialog-panel">
          <button
            type="button"
            className="custom-dress-dialog-close"
            aria-label="Fermer le dialogue"
            onClick={closeDialog}
          >
            <X aria-hidden="true" />
          </button>
          <h2 id="custom-dress-dialog-title">Comment fonctionne la confection sur mesure ?</h2>
          <ol>
            {service.steps.map((step, index) => (
              <MotionLi
                key={step}
                initial={false}
                animate={dialogOpen || reducedMotion
                  ? { opacity: 1, y: 0 }
                  : { opacity: 0, y: 8 }}
                transition={reducedMotion
                  ? { duration: 0 }
                  : { duration: 0.24, delay: index * 0.05 }}
              >
                {step}
              </MotionLi>
            ))}
          </ol>
          {service.pricingNotice && <p>{service.pricingNotice}</p>}
          <div className="custom-dress-dialog-actions">
            <Button variant="secondary" onClick={closeDialog}>Retour</Button>
            <a
              ref={continueRef}
              className="custom-dress-whatsapp-link"
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              Continuer sur WhatsApp
              <ExternalLink aria-hidden="true" />
            </a>
          </div>
        </div>
      </dialog>
    </Section>
  );
};

export default CustomDressSection;
