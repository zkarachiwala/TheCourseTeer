'use client'
import { useState, useMemo, useCallback } from 'react'
import { HeroSection } from './hero-section'
import { CourseCard, CourseCardData } from './course-card'
import { CourseRow } from './course-row'
import { CourseDetailPanel } from './course-detail-panel'
import { FeaturedUniBanner, FeaturedUniConfig } from './featured-uni-banner'
import { getArea, getAreasFromName, AREAS, AreaKey } from '@/lib/area-map'
import { useShortlist } from '@/contexts/shortlist-context'

type Layout = 'grid' | 'list' | 'compact'

interface Props {
  courses: CourseCardData[]
  universities: { slug: string; name: string }[]
  featuredUni?: FeaturedUniConfig | null
}

export function CourseListClient({ courses, universities, featuredUni }: Props) {
  const [layout, setLayout] = useState<Layout>('grid')
  const [selected, setSelected] = useState<CourseCardData | null>(null)
  const [search, setSearch] = useState('')
  const [selectedAreas, setSelectedAreas] = useState<string[]>([])
  const [selectedUnis, setSelectedUnis] = useState<string[]>([])
  const [selectedDurations, setSelectedDurations] = useState<string[]>([])
  const [minAtar, setMinAtar] = useState('')

  const { isShortlisted, toggle } = useShortlist()

  const toggleArea = useCallback((a: string) => setSelectedAreas(prev => prev.includes(a) ? prev.filter(x => x !== a) : [...prev, a]), [])
  const toggleUni = useCallback((s: string) => setSelectedUnis(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]), [])
  const toggleDuration = useCallback((d: string) => setSelectedDurations(prev => prev.includes(d) ? prev.filter(x => x !== d) : [...prev, d]), [])

  const availableDurations = useMemo(() => {
    const seen = new Set<number>()
    courses.forEach(c => { if (c.durationYears != null) seen.add(c.durationYears) })
    return Array.from(seen).sort((a, b) => a - b)
  }, [courses])

  const filtered = useMemo(() => courses.filter(c => {
    if (search) { const q = search.toLowerCase(); if (!c.name.toLowerCase().includes(q) && !c.universityName.toLowerCase().includes(q)) return false }
    if (selectedAreas.length > 0) {
      const courseAreas = [getArea(c.faculty), ...getAreasFromName(c.name)].filter(Boolean) as string[]
      if (!selectedAreas.some(a => courseAreas.includes(a))) return false
    }
    if (selectedUnis.length > 0 && !selectedUnis.includes(c.universitySlug)) return false
    if (selectedDurations.length > 0 && (c.durationYears == null || !selectedDurations.includes(String(c.durationYears)))) return false
    if (minAtar && (c.atarGuaranteed == null || c.atarGuaranteed < Number(minAtar))) return false
    return true
  }), [courses, search, selectedAreas, selectedUnis, selectedDurations, minAtar])

  const activeFilters = [
    ...selectedAreas.map(a => AREAS[a as AreaKey]?.label).filter(Boolean),
    ...selectedUnis.map(s => universities.find(u => u.slug === s)?.name ?? s),
    ...selectedDurations.map(d => `${d} yr`),
    minAtar && `ATAR ≥ ${minAtar}`,
    search && `"${search}"`,
  ].filter(Boolean) as string[]

  const clearAll = useCallback(() => { setSearch(''); setSelectedAreas([]); setSelectedUnis([]); setSelectedDurations([]); setMinAtar('') }, [])
  const closePanel = useCallback(() => setSelected(null), [])

  return (
    <>
      <HeroSection
        search={search} onSearchChange={setSearch}
        selectedAreas={selectedAreas} onAreaToggle={toggleArea}
        selectedUnis={selectedUnis} onUniToggle={toggleUni}
        selectedDurations={selectedDurations} onDurationToggle={toggleDuration}
        availableDurations={availableDurations}
        minAtar={minAtar} onMinAtarChange={setMinAtar}
        activeFilters={activeFilters} onClearAll={clearAll}
        universities={universities}
      />

      <div style={{ maxWidth: 'var(--max-w)', margin: '0 auto', padding: '16px var(--px) 8px' }}>
        {featuredUni && <FeaturedUniBanner config={featuredUni} />}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
      </div>

      <main style={{ maxWidth: 'var(--max-w)', margin: '0 auto', padding: '8px var(--px) 48px' }}>
        {layout === 'grid' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
            {filtered.map(c => (
              <CourseCard key={c.id} course={c} onClick={() => setSelected(c)} selected={selected?.id === c.id}
                onShortlist={() => toggle(c)} shortlisted={isShortlisted(c.id)}
                onAreaClick={toggleArea} onUniClick={toggleUni} />
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
                  <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text2)' }}>{c.durationYears != null ? `${c.durationYears} ${c.durationYears === 1 ? 'year' : 'years'}` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {filtered.length === 0 && (
          <p style={{ textAlign: 'center', color: 'var(--text3)', padding: '48px 0', fontSize: '15px' }}>
            No courses match your filters.{' '}
            <button onClick={clearAll} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '15px', textDecoration: 'underline' }}>Clear filters</button>
          </p>
        )}
      </main>

      {selected && <CourseDetailPanel course={selected} onClose={closePanel} />}
    </>
  )
}
