import { getMonogram } from '@/lib/area-map'

export interface FeaturedUniConfig {
  universityName: string
  tagline: string
  highlight: string
  ctaText: string
  ctaUrl: string
}

export function FeaturedUniBanner({ config }: { config: FeaturedUniConfig }) {
  return (
    <div style={{ background: 'linear-gradient(135deg, var(--accent-soft), var(--bg2))', border: '1px solid var(--accent)', borderRadius: 'var(--radius-card)', padding: '20px var(--px)', maxWidth: 'var(--max-w)', margin: '0 auto 16px', display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
      <span style={{ width: 44, height: 44, borderRadius: '10px', background: 'var(--accent)', color: 'var(--accent-fg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '14px', fontFamily: 'Manrope, sans-serif', flexShrink: 0 }}>
        {getMonogram(config.universityName)}
      </span>
      <div style={{ flex: 1, minWidth: '180px' }}>
        <p style={{ fontSize: '10px', fontWeight: 600, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.1em', margin: '0 0 2px' }}>Featured University</p>
        <p style={{ fontFamily: 'Manrope, sans-serif', fontWeight: 700, fontSize: '15px', color: 'var(--text)', margin: '0 0 1px' }}>{config.universityName}</p>
        <p style={{ fontSize: '12px', color: 'var(--text2)', margin: 0 }}>{config.tagline}</p>
      </div>
      <span style={{ fontSize: '13px', color: 'var(--text2)', flexShrink: 0 }}>{config.highlight}</span>
      <a href={config.ctaUrl} target="_blank" rel="noopener noreferrer" style={{ padding: '10px 18px', background: 'var(--accent)', color: 'var(--accent-fg)', borderRadius: 'var(--radius-btn)', fontWeight: 600, fontSize: '13px', textDecoration: 'none', flexShrink: 0 }}>
        {config.ctaText}
      </a>
    </div>
  )
}
