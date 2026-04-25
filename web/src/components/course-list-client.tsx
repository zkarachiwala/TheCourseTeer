'use client'
import { useState, useMemo, useCallback } from 'react'
import { HeroSection } from './hero-section'
import { CourseCard, CourseCardData } from './course-card'
import { CourseRow } from './course-row'
import { CourseDetailPanel } from './course-detail-panel'
import { getArea } from '@/lib/area-map'

type Layout = 'grid' | 'list' | 'compact'

interface Props {
  courses: CourseCardData[]
  universities: { slug: string; name: string }[]
  featuredUni?: { universityName: string; tagline: string; highlight: string; ctaText: string; ctaUrl: string } | null
}

export function CourseListClient({ courses, universities, featuredUni }: Props) {
  const [layout, setLayout] = useState<Layout>('grid')
  const [selected, setSelected] = useState<CourseCardData | null>(null)
  const [search, setSearch] = useState('')
  const [area, setArea] = useState('')
  const [university, setUniversity] = useState('')
  const [duration, setDuration] = useState('')
  const [minAtar, setMinAtar] = useState('')

  const filtered = useMemo(() => courses.filter(c => {
    if (search) { const q = search.toLowerCase(); if (!c.name.toLowerCase().includes(q) && !c.universityName.toLowerCase().includes(q)) return false }
    if (area && getArea(c.faculty) !== area) return false
    if (university && c.universitySlug !== university) return false
    if (duration && c.durationYears !== Number(duration)) return false
    if (minAtar && (c.atarGuaranteed == null || c.atarGuaranteed < Number(minAtar))) return false
    return true
  }), [courses, search, area, university, duration, minAtar])

  const activeFilters = [
    area && `Area: ${area}`,
    university && `Uni: ${university}`,
    duration && `${duration}yr`,
    minAtar && `ATAR ≥ ${minAtar}`,
    search && `"${search}"`,
  ].filter(Boolean) as string[]

  const clearAll = useCallback(() => { setSearch(''); setArea(''); setUniversity(''); setDuration(''); setMinAtar('') }, [])
  const closePanel = useCallback(() => setSelected(null), [])

  return (
    <>
      <HeroSection
        search={search} onSearchChange={setSearch}
        area={area} onAreaChange={setArea}
        university={university} onUniversityChange={setUniversity}
        duration={duration} onDurationChange={setDuration}
        minAtar={minAtar} onMinAtarChange={setMinAtar}
        activeFilters={activeFilters} onClearAll={clearAll}
        universities={universities}
      />

      <div style={{ maxWidth: 'var(--max-w)', margin: '0 auto', padding: '16px var(--px)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <p style={{ fontSize: '14px', color: 'var(--text2)', margin: 0 }}>
          {filtered.length} {filtered.length === 1 ? 'course' : 'courses'}
        </p>
        <div style={{ display: 'flex', gap: '4px', background: 'var(--bg2)', borderRadius: '10px', padding: '4px' }}>
          {(['grid', 'list', 'compact'] as Layout[]).map(l => (
            <button key={l} onClick={() => setLayout(l)} style={{ padding: '6px 12px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontSize: '12px', background: layout === l ? 'var(--accent)' : 'transparent', color: layout === l ? 'var(--accent-fg)' : 'var(--text2)' }}>
              {l === 'grid' ? '⊞ Grid' : l === 'list' ? '☰ List' : '≡ Compact'}
            </button>
          ))}
        </div>
      </div>

      <main style={{ maxWidth: 'var(--max-w)', margin: '0 auto', padding: '0 var(--px) 48px' }}>
        {layout === 'grid' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
            {filtered.map(c => (
              <CourseCard key={c.id} course={c} onClick={() => setSelected(c)} selected={selected?.id === c.id} />
            ))}
          </div>
        )}
        {layout === 'list' && (
          <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-card)', overflow: 'hidden' }}>
            {filtered.map(c => (
              <CourseRow key={c.id} course={c} onClick={() => setSelected(c)} selected={selected?.id === c.id} />
            ))}
          </div>
        )}
        {layout === 'compact' && (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>{['Course', 'University', 'ATAR', 'Campus', 'Duration'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase', borderBottom: '2px solid var(--border)' }}>{h}</th>
              ))}</tr>
            </thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} onClick={() => setSelected(c)} style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer', background: selected?.id === c.id ? 'var(--accent-soft)' : 'transparent' }}>
                  <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>{c.name}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text2)' }}>{c.universityName}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 700, color: 'var(--text2)' }}>{c.atarGuaranteed ?? '—'}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text2)' }}>{c.campusName ?? '—'}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text2)' }}>{c.durationYears != null ? `${c.durationYears}yr` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {filtered.length === 0 && (
          <p style={{ textAlign: 'center', color: 'var(--text3)', padding: '48px 0', fontSize: '15px' }}>
            No courses match your filters. <button onClick={clearAll} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '15px', textDecoration: 'underline' }}>Clear filters</button>
          </p>
        )}
      </main>

      {selected && <CourseDetailPanel course={selected} onClose={closePanel} />}
    </>
  )
}
