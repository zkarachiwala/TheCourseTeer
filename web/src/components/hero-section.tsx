'use client'
import { useEffect, useState } from 'react'
import { AREAS } from '@/lib/area-map'

const CYCLING_WORDS = ['Engineering', 'Medicine', 'Business', 'Law', 'Design', 'Science', 'Education']

interface HeroSectionProps {
  search: string; onSearchChange: (v: string) => void
  area: string; onAreaChange: (v: string) => void
  university: string; onUniversityChange: (v: string) => void
  duration: string; onDurationChange: (v: string) => void
  minAtar: string; onMinAtarChange: (v: string) => void
  activeFilters: string[]; onClearAll: () => void
  universities: { slug: string; name: string }[]
}

export function HeroSection(props: HeroSectionProps) {
  const { search, onSearchChange, area, onAreaChange, university, onUniversityChange, duration, onDurationChange, minAtar, onMinAtarChange, activeFilters, onClearAll, universities } = props
  const [wordIdx, setWordIdx] = useState(0)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const t = setInterval(() => {
      setVisible(false)
      setTimeout(() => { setWordIdx(i => (i + 1) % CYCLING_WORDS.length); setVisible(true) }, 300)
    }, 2000)
    return () => clearInterval(t)
  }, [])

  return (
    <section style={{ background: 'linear-gradient(135deg, var(--bg2) 0%, var(--bg) 100%)', padding: '64px var(--px) 40px', textAlign: 'center' }}>
      <p style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '16px' }}>
        Victorian Universities · Undergraduate
      </p>
      <h1 style={{ fontFamily: 'Manrope, sans-serif', fontSize: 'clamp(28px, 5vw, 52px)', fontWeight: 300, color: 'var(--text)', lineHeight: 1.2, marginBottom: '32px' }}>
        Find your degree in{' '}
        <span data-testid="cycling-word" style={{ fontWeight: 800, color: 'var(--accent)', display: 'inline-block', opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(-8px)', transition: 'opacity 0.3s, transform 0.3s' }}>
          {CYCLING_WORDS[wordIdx]}
        </span>
      </h1>

      <div style={{ maxWidth: '640px', margin: '0 auto 24px', position: 'relative' }}>
        <input
          type="text" placeholder="Search courses, universities, fields..."
          value={search} onChange={e => onSearchChange(e.target.value)}
          style={{ width: '100%', padding: '14px 20px 14px 48px', borderRadius: 'var(--radius-pill)', border: '1.5px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)', fontSize: '16px', outline: 'none', boxSizing: 'border-box' }}
        />
        <svg style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', width: 20, height: 20, color: 'var(--text3)', pointerEvents: 'none' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '16px' }}>
        <FilterSelect value={area} onChange={onAreaChange} placeholder="All Areas">
          {Object.entries(AREAS).map(([k, { label }]) => <option key={k} value={k}>{label}</option>)}
        </FilterSelect>
        <FilterSelect value={university} onChange={onUniversityChange} placeholder="All Universities">
          {universities.map(u => <option key={u.slug} value={u.slug}>{u.name}</option>)}
        </FilterSelect>
        <FilterSelect value={duration} onChange={onDurationChange} placeholder="Any Duration">
          <option value="3">3 years</option>
          <option value="4">4 years</option>
          <option value="5">5 years</option>
        </FilterSelect>
        <input type="number" placeholder="Min ATAR" value={minAtar} onChange={e => onMinAtarChange(e.target.value)}
          min={0} max={99.95} step={0.05} style={{ ...selectStyle, width: '110px' }} />
      </div>

      {activeFilters.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap', alignItems: 'center' }}>
          {activeFilters.map(f => (
            <span key={f} style={{ background: 'var(--accent-soft)', color: 'var(--accent)', fontSize: '12px', fontWeight: 600, padding: '4px 12px', borderRadius: 'var(--radius-pill)', animation: 'scaleIn 0.2s both' }}>{f}</span>
          ))}
          <button onClick={onClearAll} style={{ fontSize: '12px', color: 'var(--text3)', background: 'transparent', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
            Clear all
          </button>
        </div>
      )}
    </section>
  )
}

const selectStyle: React.CSSProperties = { padding: '10px 16px', borderRadius: 'var(--radius-pill)', border: '1.5px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)', fontSize: '14px', cursor: 'pointer', outline: 'none' }

function FilterSelect({ value, onChange, placeholder, children }: { value: string; onChange: (v: string) => void; placeholder: string; children: React.ReactNode }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)} style={selectStyle}>
      <option value="">{placeholder}</option>
      {children}
    </select>
  )
}
