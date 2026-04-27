'use client'
import { useEffect, useRef, useState } from 'react'
import { AREAS, AreaKey } from '@/lib/area-map'

const CYCLING_WORDS = ['Engineering', 'Medicine', 'Business', 'Law', 'Design', 'Science', 'Education']

const SORTED_AREAS = Object.entries(AREAS).sort(([, a], [, b]) => a.label.localeCompare(b.label)) as [AreaKey, { label: string; color: string }][]

interface HeroSectionProps {
  search: string; onSearchChange: (v: string) => void
  selectedAreas: string[]; onAreaToggle: (a: string) => void
  selectedUnis: string[]; onUniToggle: (s: string) => void
  selectedDurations: string[]; onDurationToggle: (d: string) => void
  availableDurations: number[]
  minAtar: string; onMinAtarChange: (v: string) => void
  activeFilters: string[]; onClearAll: () => void
  universities: { slug: string; name: string }[]
}

export function HeroSection(props: HeroSectionProps) {
  const { search, onSearchChange, selectedAreas, onAreaToggle, selectedUnis, onUniToggle, selectedDurations, onDurationToggle, availableDurations, minAtar, onMinAtarChange, activeFilters, onClearAll, universities } = props
  const [wordIdx, setWordIdx] = useState(0)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const t = setInterval(() => {
      setVisible(false)
      setTimeout(() => { setWordIdx(i => (i + 1) % CYCLING_WORDS.length); setVisible(true) }, 300)
    }, 2000)
    return () => clearInterval(t)
  }, [])

  const sortedUnis = [...universities].sort((a, b) => a.name.localeCompare(b.name))
  const sortedDurations = [...availableDurations].sort((a, b) => a - b)

  return (
    <section style={{ background: 'linear-gradient(135deg, var(--bg2) 0%, var(--bg) 100%)', padding: '64px var(--px) 40px', textAlign: 'center' }}>
      <p style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '16px' }}>
        Victorian Universities
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

      {/* Area toggle pills */}
      <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '16px', maxWidth: '760px', margin: '0 auto 16px' }}>
        {SORTED_AREAS.map(([key, { label, color }]) => {
          const active = selectedAreas.includes(key)
          return (
            <button key={key} onClick={() => onAreaToggle(key)} style={{ padding: '6px 14px', borderRadius: 'var(--radius-pill)', border: `1.5px solid ${active ? color : 'var(--border)'}`, background: active ? color : 'var(--card-bg)', color: active ? '#fff' : 'var(--text2)', fontSize: '13px', fontWeight: active ? 600 : 400, cursor: 'pointer', transition: 'all 0.15s' }}>
              {label}
            </button>
          )
        })}
      </div>

      {/* Secondary filters */}
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '16px' }}>
        <UniMultiSelect universities={sortedUnis} selected={selectedUnis} onToggle={onUniToggle} />

        {/* Duration toggle pills */}
        {sortedDurations.length > 0 && (
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            {sortedDurations.map(d => {
              const val = String(d)
              const active = selectedDurations.includes(val)
              return (
                <button key={val} onClick={() => onDurationToggle(val)} style={{ padding: '8px 12px', borderRadius: 'var(--radius-pill)', border: `1.5px solid ${active ? 'var(--accent)' : 'var(--border)'}`, background: active ? 'var(--accent)' : 'var(--card-bg)', color: active ? 'var(--accent-fg)' : 'var(--text2)', fontSize: '13px', fontWeight: active ? 600 : 400, cursor: 'pointer', transition: 'all 0.15s', whiteSpace: 'nowrap' }}>
                  {d === 1 ? '1 yr' : `${d} yrs`}
                </button>
              )
            })}
          </div>
        )}

        <input type="number" placeholder="Min ATAR" value={minAtar} onChange={e => onMinAtarChange(e.target.value)}
          min={0} max={99.95} step={0.05}
          style={{ padding: '8px 14px', borderRadius: 'var(--radius-pill)', border: '1.5px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)', fontSize: '13px', outline: 'none', width: '110px' }} />
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

function UniMultiSelect({ universities, selected, onToggle }: { universities: { slug: string; name: string }[]; selected: string[]; onToggle: (s: string) => void }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const label = selected.length === 0 ? 'All Universities' : selected.length === 1
    ? (universities.find(u => u.slug === selected[0])?.name ?? '1 selected')
    : `${selected.length} universities`

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button onClick={() => setOpen(v => !v)} style={{ padding: '8px 14px', borderRadius: 'var(--radius-pill)', border: `1.5px solid ${selected.length > 0 ? 'var(--accent)' : 'var(--border)'}`, background: selected.length > 0 ? 'var(--accent-soft)' : 'var(--card-bg)', color: selected.length > 0 ? 'var(--accent)' : 'var(--text2)', fontSize: '13px', fontWeight: selected.length > 0 ? 600 : 400, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap' }}>
        {label}
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s', flexShrink: 0 }}>
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {open && (
        <div style={{ position: 'absolute', top: 'calc(100% + 6px)', left: '50%', transform: 'translateX(-50%)', background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '12px', boxShadow: 'var(--shadow-lg)', zIndex: 200, minWidth: '220px', overflow: 'hidden' }}>
          {universities.map(u => {
            const checked = selected.includes(u.slug)
            return (
              <label key={u.slug} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '9px 14px', cursor: 'pointer', background: checked ? 'var(--accent-soft)' : 'transparent', fontSize: '13px', color: checked ? 'var(--accent)' : 'var(--text)', fontWeight: checked ? 600 : 400 }}>
                <input type="checkbox" checked={checked} onChange={() => onToggle(u.slug)} style={{ accentColor: 'var(--accent)', width: 14, height: 14, flexShrink: 0 }} />
                {u.name}
              </label>
            )
          })}
        </div>
      )}
    </div>
  )
}
