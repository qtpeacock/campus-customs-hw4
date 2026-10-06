import { useId } from 'react'

/** Campus Customs shield monogram: a navy shield with a white keyline and serif "CC". */
export function ShieldMark({ size = 40 }: { size?: number }) {
  return (
    <svg viewBox="0 0 40 46" width={size} height={size * 1.15} aria-hidden="true" className="shield-mark">
      <path d="M20 1.5 37.5 6.5V22c0 11-7.6 18.6-17.5 22.5C10.1 40.6 2.5 33 2.5 22V6.5L20 1.5Z" fill="#00366b" />
      <path
        d="M20 4.6 34.6 8.8V22c0 9.2-6.2 15.6-14.6 19.2C11.6 37.6 5.4 31.2 5.4 22V8.8L20 4.6Z"
        fill="none"
        stroke="#ffffff"
        strokeWidth="1.2"
      />
      <text
        x="20"
        y="28.5"
        textAnchor="middle"
        fontFamily="'Libre Caslon Display', Georgia, serif"
        fontSize="16"
        fill="#ffffff"
        letterSpacing="0.5"
      >
        CC
      </text>
    </svg>
  )
}

/**
 * A round "seal" badge with the shop's name and New Haven around the edge (SVG text on a circle).
 * Used as a quiet varsity detail in the hero and footer.
 */
export function Seal({ size = 132, light = false }: { size?: number; light?: boolean }) {
  const ink = light ? '#ffffff' : '#00366b'
  const circleId = `seal-circle-${useId().replace(/:/g, '')}`
  return (
    <svg viewBox="0 0 120 120" width={size} height={size} role="img" aria-label="Campus Customs, New Haven, since the 1970s" className="seal">
      <defs>
        <path id={circleId} d="M60 60m-44 0a44 44 0 1 1 88 0a44 44 0 1 1 -88 0" />
      </defs>
      <circle cx="60" cy="60" r="57" fill="none" stroke={ink} strokeWidth="1.5" />
      <circle cx="60" cy="60" r="31" fill="none" stroke={ink} strokeWidth="1" />
      <text fontFamily="'Barlow Condensed', 'Arial Narrow', sans-serif" fontSize="11.5" fontWeight="600" letterSpacing="3.1" fill={ink}>
        <textPath href={`#${circleId}`}>CAMPUS CUSTOMS · NEW HAVEN · SINCE THE 1970s ·</textPath>
      </text>
      <text x="60" y="68" textAnchor="middle" fontFamily="'Libre Caslon Display', Georgia, serif" fontSize="24" fill={ink}>
        CC
      </text>
    </svg>
  )
}
