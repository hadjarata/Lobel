import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Pause, Play } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { getHomeHero } from '../../api/homeContent';
import { Container } from '../ui';
import { springSnappy } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';
import './HeroSection.css';

const MotionDiv = motion.div;
const MotionH1 = motion.h1;
const MotionImg = motion.img;
const MotionP = motion.p;
const MotionVideo = motion.video;

const FALLBACK = {
  title: 'Bienvenue sur LobelStore',
  description: 'Découvrez notre sélection de créations et explorez notre boutique.',
  mediaType: null,
  mediaUrl: null,
};

const HeroSection = () => {
  const [hero, setHero] = useState(FALLBACK);
  const [mediaFailed, setMediaFailed] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  const videoRef = useRef(null);
  const manuallyPaused = useRef(false);
  const resumeAfterVisibility = useRef(false);
  const entranceTransition = useMotionTransition(springSnappy);

  useEffect(() => {
    const controller = new AbortController();
    getHomeHero({ signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted && value) setHero(value);
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const sync = () => setReducedMotion(media.matches);
    media.addEventListener('change', sync);
    return () => media.removeEventListener('change', sync);
  }, []);

  useEffect(() => {
    const onVisibility = () => {
      const video = videoRef.current;
      if (!video) return;
      if (document.hidden) {
        resumeAfterVisibility.current = !video.paused && !manuallyPaused.current;
        video.pause();
      } else if (
        resumeAfterVisibility.current && !manuallyPaused.current && !reducedMotion
      ) {
        video.play().catch(() => {});
      }
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, [reducedMotion]);

  const toggleVideo = () => {
    const video = videoRef.current;
    if (!video || mediaFailed) return;
    if (video.paused) {
      manuallyPaused.current = false;
      video.play().catch(() => {});
    } else {
      manuallyPaused.current = true;
      video.pause();
    }
  };

  const showVideo = hero.mediaType === 'VIDEO'
    && hero.mediaUrl && !mediaFailed && !reducedMotion;
  const showImage = hero.mediaType === 'IMAGE' && hero.mediaUrl && !mediaFailed;
  const contentVariants = {
    hidden: {},
    visible: {
      transition: reducedMotion
        ? { staggerChildren: 0 }
        : { staggerChildren: 0.1, delayChildren: 0.12 },
    },
  };
  const contentItemVariants = {
    hidden: reducedMotion ? { opacity: 1 } : { opacity: 0, y: 16 },
    visible: {
      opacity: 1,
      y: 0,
      transition: entranceTransition,
    },
  };

  return (
    <section className="hero-section" aria-label="Présentation LobelStore">
      <div className="hero-media" aria-hidden="true">
        {showVideo && (
          <MotionVideo
            ref={videoRef}
            autoPlay
            muted
            loop
            playsInline
            preload="metadata"
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onError={() => { setMediaFailed(true); setPlaying(false); }}
            initial={reducedMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: reducedMotion ? 0 : 0.45 }}
          >
            <source src={hero.mediaUrl} type="video/mp4" />
          </MotionVideo>
        )}
        {showImage && (
          <MotionImg
            src={hero.mediaUrl}
            alt=""
            onError={() => setMediaFailed(true)}
            initial={reducedMotion ? false : { opacity: 0.7, scale: 1 }}
            animate={reducedMotion
              ? { opacity: 1, scale: 1 }
              : { opacity: 1, scale: 1.045 }}
            transition={reducedMotion
              ? { duration: 0 }
              : {
                opacity: { duration: 0.45 },
                scale: { duration: 18, ease: 'linear' },
              }}
          />
        )}
      </div>
      <div className="hero-overlay" aria-hidden="true" />
      <Container className="hero-content">
        <MotionDiv
          className="hero-text"
          variants={contentVariants}
          initial="hidden"
          animate="visible"
        >
          <MotionH1 className="hero-title" variants={contentItemVariants}>
            {hero.title}
          </MotionH1>
          <MotionP className="hero-subtitle" variants={contentItemVariants}>
            {hero.description}
          </MotionP>
          <MotionDiv className="hero-actions" variants={contentItemVariants}>
            <Link className="hero-cta" to="/shop">Voir la boutique</Link>
          </MotionDiv>
        </MotionDiv>
      </Container>
      <a className="hero-scroll-indicator" href="#new-products" aria-label="Découvrir les nouveautés">
        <span>Découvrir</span>
        <ChevronDown aria-hidden="true" />
      </a>
      {showVideo && (
        <button
          type="button"
          className="hero-video-control"
          onClick={toggleVideo}
          aria-label={playing ? 'Mettre la vidéo en pause' : 'Lire la vidéo'}
        >
          {playing ? <Pause aria-hidden="true" /> : <Play aria-hidden="true" />}
        </button>
      )}
    </section>
  );
};

export default HeroSection;
