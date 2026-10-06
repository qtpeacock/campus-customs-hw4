import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { HERO_SLIDES } from '../heroSlides.ts'

const SLIDE_MS = 6000
const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

/**
 * Home page hero: Yale photos crossfade behind the headline under a dark overlay, so the text stays readable.
 * Auto-advances every 6 seconds (not for visitors who prefer reduced motion) and has a pause button and dots,
 * so moving content can always be stopped.
 */
export default function HeroCarousel({ children }: { children: ReactNode }) {
  // `loaded`: photos that have been shown plus the next one. Only those are mounted, so the page doesn't
  // download all five at once, and the upcoming photo is ready before the crossfade.
  const [{ index, loaded }, setSlides] = useState(() => ({ index: 0, loaded: [0, 1] }))
  const [paused, setPaused] = useState(prefersReducedMotion)

  function show(next: number) {
    setSlides((current) => ({
      index: next,
      loaded: [...new Set([...current.loaded, next, (next + 1) % HERO_SLIDES.length])],
    }))
  }

  useEffect(() => {
    if (paused) return
    const timer = window.setInterval(() => {
      setSlides((current) => {
        const next = (current.index + 1) % HERO_SLIDES.length
        return { index: next, loaded: [...new Set([...current.loaded, next, (next + 1) % HERO_SLIDES.length])] }
      })
    }, SLIDE_MS)
    return () => window.clearInterval(timer)
  }, [paused])

  const slide = HERO_SLIDES[index]

  return (
    <section className="hero hero-carousel" aria-roledescription="carousel" aria-label="Yale photos">
      <div className="hero-slides">
        {HERO_SLIDES.map((s, i) =>
          loaded.includes(i) ? (
            <img
              key={s.src}
              src={s.src}
              alt={i === index ? s.alt : ''}
              aria-hidden={i !== index}
              className={i === index ? 'hero-slide active' : 'hero-slide'}
              decoding="async"
            />
          ) : null,
        )}
        <div className="hero-overlay" aria-hidden="true" />
      </div>

      <div className="container hero-inner">{children}</div>

      <div className="container hero-controls">
        <div className="hero-nav">
          <button
            type="button"
            className="hero-pause"
            onClick={() => setPaused((p) => !p)}
            aria-label={paused ? 'Play slideshow' : 'Pause slideshow'}
          >
            {paused ? (
              <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
                <path fill="currentColor" d="M7 4l13 8-13 8V4Z" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
                <path fill="currentColor" d="M6 4h4v16H6V4Zm8 0h4v16h-4V4Z" />
              </svg>
            )}
          </button>
          {HERO_SLIDES.map((s, i) => (
            <button
              key={s.src}
              type="button"
              className={i === index ? 'hero-dot active' : 'hero-dot'}
              onClick={() => show(i)}
              aria-label={`Show photo ${i + 1} of ${HERO_SLIDES.length}: ${s.alt}`}
              aria-current={i === index}
            />
          ))}
        </div>
        <p className="hero-credit">
          Photo:{' '}
          <a href={slide.source} target="_blank" rel="noreferrer">
            {slide.author}
          </a>
          ,{' '}
          <a href={slide.licenseUrl} target="_blank" rel="noreferrer">
            {slide.license}
          </a>
        </p>
      </div>
    </section>
  )
}
