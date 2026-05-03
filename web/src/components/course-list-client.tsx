'use client'
import { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { HeroSection } from './hero-section'
import { CourseCard, CourseCardData } from './course-card'
import { CourseRow } from './course-row'
import { CourseDetailPanel } from './course-detail-panel'
import { FeaturedUniBanner, FeaturedUniConfig } from './featured-uni-banner'
import { AREAS, AreaKey } from '@/lib/area-map'
import { useShortlist } from '@/contexts/shortlist-context'
import type { FetchCoursePageParams } from '@/lib/queries/courses'

type Layout = 'grid' | 'list' | 'compact'

interface Props {
  courses: CourseCardData[]
  total: number
  availableDurations: number[]
  universities: { slug: string; name: string }[]
  currentParams: FetchCoursePageParams
  featuredUni?: FeaturedUniConfig | null
}

export function CourseListClient({
  courses,
  total,
  availableDurations,
  universities,
  currentParams,
  featuredUni,
}: Props) {
  const router = useRouter()
  const pathname = usePathname()
  const [layout, setLayout] = useState<Layout>('grid')

  function navigate(url: string, opts?: { scroll?: boolean }) {
    router.replace(url, opts)
    router.refresh()
  }
  const [selected, setSelected] = useState<CourseCardData | null>(null)
  const { isShortlisted, toggle } = useShortlist()

  function buildUrl(patch: {
    page?: number
    pageSize?: number
    search?: string
    areas?: string[]
    unis?: string[]
    durations?: string[]
    minAtar?: number | string | undefined
  }): string {
    const f = currentParams.filters
    const sp = new URLSearchParams()
    const page = patch.page ?? currentParams.page
    const pageSize = patch.pageSize ?? currentParams.pageSize
    const search = 'search' in patch ? patch.search : f.search
    const areas = 'areas' in patch ? patch.areas : f.areas
    const unis = 'unis' in patch ? patch.unis : f.unis
    const durations = 'durations' in patch ? patch.durations : f.durations
    const minAtar =
      'minAtar' in patch
        ? patch.minAtar
        : f.minAtar
          ? String(f.minAtar)
          : undefined

    if (page > 1) sp.set('page', String(page))
    if (pageSize !== 48) sp.set('pageSize', String(pageSize))
    if (search) sp.set('search', search)
    if (areas?.length) sp.set('areas', areas.join(','))
    if (unis?.length) sp.set('unis', unis.join(','))
    if (durations?.length) sp.set('durations', durations.join(','))
    if (minAtar) sp.set('minAtar', String(minAtar))

    const qs = sp.toString()
    return pathname + (qs ? '?' + qs : '')
  }

  const toggleArea = (a: string) => {
    const areas = currentParams.filters.areas ?? []
    navigate(
      buildUrl({ areas: areas.includes(a) ? areas.filter(x => x !== a) : [...areas, a], page: 1 }),
      { scroll: false }
    )
  }

  const toggleUni = (s: string) => {
    const unis = currentParams.filters.unis ?? []
    navigate(
      buildUrl({ unis: unis.includes(s) ? unis.filter(x => x !== s) : [...unis, s], page: 1 }),
      { scroll: false }
    )
  }

  const toggleDuration = (d: string) => {
    const durations = currentParams.filters.durations ?? []
    navigate(
      buildUrl({
        durations: durations.includes(d) ? durations.filter(x => x !== d) : [...durations, d],
        page: 1,
      }),
      { scroll: false }
    )
  }

  const clearAll = () =>
    navigate(
      buildUrl({ search: undefined, areas: [], unis: [], durations: [], minAtar: undefined, page: 1 }),
      { scroll: false }
    )

  const activeFilters = [
    ...(currentParams.filters.areas ?? []).map(a => AREAS[a as AreaKey]?.label).filter(Boolean),
    ...(currentParams.filters.unis ?? []).map(s => universities.find(u => u.slug === s)?.name ?? s),
    ...(currentParams.filters.durations ?? []).map(d => `${d} yr`),
    currentParams.filters.minAtar && `ATAR ≥ ${currentParams.filters.minAtar}`,
    currentParams.filters.search && `"${currentParams.filters.search}"`,
  ].filter(Boolean) as string[]

  const totalPages = Math.ceil(total / currentParams.pageSize)
  const page = currentParams.page

  return (
    <>
      <HeroSection
        search={currentParams.filters.search ?? ''}
        onSearchChange={v =>
          navigate(buildUrl({ search: v || undefined, page: 1 }), { scroll: false })
        }
        selectedAreas={currentParams.filters.areas ?? []}
        onAreaToggle={toggleArea}
        selectedUnis={currentParams.filters.unis ?? []}
        onUniToggle={toggleUni}
        selectedDurations={currentParams.filters.durations ?? []}
        onDurationToggle={toggleDuration}
        availableDurations={availableDurations}
        minAtar={currentParams.filters.minAtar ? String(currentParams.filters.minAtar) : ''}
        onMinAtarChange={v =>
          navigate(
            buildUrl({ minAtar: v ? Number(v) : undefined, page: 1 }),
            { scroll: false }
          )
        }
        activeFilters={activeFilters}
        onClearAll={clearAll}
        universities={universities}
      />

      <div style={{ maxWidth: 'var(--max-w)', margin: '0 auto', padding: '16px var(--px) 8px' }}>
        {featuredUni && <FeaturedUniBanner config={featuredUni} />}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ fontSize: '14px', color: 'var(--text2)', margin: 0 }}>
            {total} {total === 1 ? 'course' : 'courses'}
          </p>
          <div style={{ display: 'flex', gap: '4px', background: 'var(--bg2)', borderRadius: '10px', padding: '4px' }}>
            {(['grid', 'list', 'compact'] as Layout[]).map(l => (
              <button
                key={l}
                onClick={() => setLayout(l)}
                style={{
                  padding: '6px 12px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                  fontSize: '12px', background: layout === l ? 'var(--accent)' : 'transparent',
                  color: layout === l ? 'var(--accent-fg)' : 'var(--text2)',
                }}
              >
                {l === 'grid' ? '⊞ Grid' : l === 'list' ? '☰ List' : '≡ Compact'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {totalPages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', justifyContent: 'center', padding: '8px 0', maxWidth: 'var(--max-w)', margin: '0 auto' }}>
          <button
            disabled={page <= 1}
            onClick={() => navigate(buildUrl({ page: page - 1 }), { scroll: true })}
            style={{ padding: '6px 14px', borderRadius: 'var(--radius-btn)', border: '1.5px solid var(--border)', background: 'var(--card-bg)', color: page <= 1 ? 'var(--text3)' : 'var(--text)', cursor: page <= 1 ? 'default' : 'pointer', fontSize: '13px' }}
          >
            ← Prev
          </button>
          <span style={{ fontSize: '13px', color: 'var(--text2)' }}>
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => navigate(buildUrl({ page: page + 1 }), { scroll: true })}
            style={{ padding: '6px 14px', borderRadius: 'var(--radius-btn)', border: '1.5px solid var(--border)', background: 'var(--card-bg)', color: page >= totalPages ? 'var(--text3)' : 'var(--text)', cursor: page >= totalPages ? 'default' : 'pointer', fontSize: '13px' }}
          >
            Next →
          </button>
          <select
            value={currentParams.pageSize}
            onChange={e =>
              navigate(buildUrl({ pageSize: Number(e.target.value), page: 1 }), { scroll: false })
            }
            style={{ padding: '6px 10px', borderRadius: 'var(--radius-btn)', border: '1.5px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text2)', fontSize: '13px', cursor: 'pointer' }}
          >
            {[24, 48, 72, 96].map(n => (
              <option key={n} value={n}>{n} per page</option>
            ))}
          </select>
        </div>
      )}

      <main style={{ maxWidth: 'var(--max-w)', margin: '0 auto', padding: '8px var(--px) 48px' }}>
        {layout === 'grid' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
            {courses.map(c => (
              <CourseCard
                key={c.id}
                course={c}
                onClick={() => setSelected(c)}
                selected={selected?.id === c.id}
                onShortlist={() => toggle(c)}
                shortlisted={isShortlisted(c.id)}
                onAreaClick={toggleArea}
                onUniClick={toggleUni}
              />
            ))}
          </div>
        )}
        {layout === 'list' && (
          <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-card)', overflow: 'hidden' }}>
            {courses.map(c => (
              <CourseRow key={c.id} course={c} onClick={() => setSelected(c)} selected={selected?.id === c.id} />
            ))}
          </div>
        )}
        {layout === 'compact' && (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Course', 'University', 'ATAR', 'Campus', 'Duration'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase', borderBottom: '2px solid var(--border)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {courses.map(c => (
                <tr
                  key={c.id}
                  onClick={() => setSelected(c)}
                  style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer', background: selected?.id === c.id ? 'var(--accent-soft)' : 'transparent' }}
                >
                  <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>{c.name}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text2)' }}>{c.universityName}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 700, color: 'var(--text2)' }}>{c.atarSelectionRank ?? c.atarGuaranteed ?? '—'}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text2)' }}>{c.campusName ?? '—'}</td>
                  <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text2)' }}>{c.durationYears != null ? `${c.durationYears} ${c.durationYears === 1 ? 'year' : 'years'}` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {courses.length === 0 && (
          <p style={{ textAlign: 'center', color: 'var(--text3)', padding: '48px 0', fontSize: '15px' }}>
            No courses match your filters.{' '}
            <button onClick={clearAll} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '15px', textDecoration: 'underline' }}>
              Clear filters
            </button>
          </p>
        )}
      </main>

      {selected && <CourseDetailPanel course={selected} onClose={() => setSelected(null)} />}
    </>
  )
}
