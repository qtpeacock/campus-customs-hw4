import { useState } from 'react'

interface GalleryProps {
  name: string
  image: string
  /** Extra photos (someone wearing it). With none, the gallery is just the product photo. */
  extras: string[]
}

/** Large product photo with thumbnails and arrows to toggle to any "worn on campus" photos. */
export default function ProductGallery({ name, image, extras }: GalleryProps) {
  const photos = [
    { src: image, label: 'Product', kind: 'product' },
    ...extras.map((src) => ({ src, label: 'Worn on campus', kind: 'worn' })),
  ]
  const [index, setIndex] = useState(0)
  const current = photos[index]
  const step = (delta: number) => setIndex((i) => (i + delta + photos.length) % photos.length)

  return (
    <div className="product-gallery">
      <div className={`product-detail-image ${current.kind}`}>
        {photos.map((photo, i) => (
          <img
            key={photo.src}
            src={photo.src}
            alt={i === index ? (photo.kind === 'worn' ? `${name}, worn on campus` : name) : ''}
            aria-hidden={i !== index}
            className={i === index ? `gallery-img ${photo.kind} active` : `gallery-img ${photo.kind}`}
          />
        ))}
        {photos.length > 1 && (
          <>
            <button type="button" className="gallery-arrow prev" onClick={() => step(-1)} aria-label="Previous photo">
              ‹
            </button>
            <button type="button" className="gallery-arrow next" onClick={() => step(1)} aria-label="Next photo">
              ›
            </button>
            <span className="gallery-count" aria-live="polite">
              {index + 1} / {photos.length} · {current.label}
            </span>
          </>
        )}
      </div>

      {photos.length > 1 && (
        <div className="gallery-thumbs" role="group" aria-label="Product photos">
          {photos.map((photo, i) => (
            <button
              key={photo.src}
              type="button"
              className={i === index ? `gallery-thumb ${photo.kind} active` : `gallery-thumb ${photo.kind}`}
              onClick={() => setIndex(i)}
              aria-label={`Show photo ${i + 1}: ${photo.label}`}
              aria-pressed={i === index}
            >
              <img src={photo.src} alt="" />
              <span>{photo.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
