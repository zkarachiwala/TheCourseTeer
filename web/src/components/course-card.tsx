import { getArea, getAreasFromName, getMonogram, atarColor, degreeLabel, AREAS, AreaKey } from '@/lib/area-map'

export interface CourseCardData {
  id: string; name: string; faculty: string | null
  universityName: string; universitySlug: string
  degreeType: string | null; durationYears: number | null
  sourceUrl: string | null; atarGuaranteed: number | null
  campusName: string | null
}

interface Props {
  course: CourseCardData; onClick: () => void; selected?: boolean
  onShortlist?: () => void; shortlisted?: boolean
  onAreaClick?: (area: string) => void
  onUniClick?: (slug: string) => void
}

export function CourseCard({ course, onClick, selected, onShortlist, shortlisted, onAreaClick, onUniClick }: Props) {
  const primaryArea = getArea(course.faculty)
  const nameAreas = getAreasFromName(course.name)
  const allAreaKeys = primaryArea
    ? [primaryArea, ...nameAreas.filter(a => a !== primaryArea)]
    : nameAreas
  const uniqueAreaKeys = [...new Set(allAreaKeys)] as AreaKey[]

  const durationText = course.durationYears != null
    ? `${course.durationYears} ${course.durationYears === 1 ? 'year' : 'years'}`
    : null

  return (
    <article onClick={onClick} style={{ background: 'var(--card-bg)', borderRadius: 'var(--radius-card)', border: `1.5px solid ${selected ? 'var(--accent)' : 'var(--border)'}`, padding: '20px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '10px', boxShadow: selected ? 'var(--shadow-lg)' : 'var(--shadow)', transition: 'all 0.2s' }}>

      {/* Row 1: area pills left, ATAR right */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', minHeight: '22px', flexWrap: 'wrap' }}>
        {uniqueAreaKeys.map(key => {
          const area = AREAS[key]
          return (
            <span key={key} onClick={e => { e.stopPropagation(); onAreaClick?.(key) }} style={{ background: area.color, color: '#fff', fontSize: '11px', fontWeight: 600, padding: '2px 10px', borderRadius: 'var(--radius-pill)', flexShrink: 0, cursor: onAreaClick ? 'pointer' : 'default' }}>
              {area.label}
            </span>
          )
        })}
        {course.atarGuaranteed != null && (
          <span style={{ fontSize: '13px', fontWeight: 700, color: atarColor(course.atarGuaranteed), flexShrink: 0, marginLeft: 'auto' }}>
            ATAR {course.atarGuaranteed}
          </span>
        )}
      </div>

      {/* Row 2: course name */}
      <h3 style={{ fontFamily: 'Manrope, sans-serif', fontWeight: 700, fontSize: '15px', color: 'var(--text)', lineHeight: 1.3, margin: 0, flex: 1 }}>{course.name}</h3>

      {/* Row 3: university monogram + name + campus */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span
          onClick={e => { e.stopPropagation(); onUniClick?.(course.universitySlug) }}
          style={{ width: 32, height: 32, borderRadius: '8px', background: 'var(--accent-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '11px', color: 'var(--accent)', flexShrink: 0, cursor: onUniClick ? 'pointer' : 'default' }}
        >
          {getMonogram(course.universityName)}
        </span>
        <div>
          <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text2)', margin: 0 }}>{course.universityName}</p>
          {course.campusName && <p style={{ fontSize: '12px', color: 'var(--text3)', margin: 0 }}>📍 {course.campusName}</p>}
        </div>
      </div>

      {/* Row 4: duration + degree type left, save button right */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minHeight: '26px' }}>
        {(durationText || course.degreeType) && (
          <p style={{ fontSize: '12px', color: 'var(--text3)', margin: 0 }}>
            {[durationText, degreeLabel(course.degreeType)].filter(Boolean).join(' · ')}
          </p>
        )}
        {onShortlist && (
          <button
            onClick={e => { e.stopPropagation(); onShortlist() }}
            aria-label={shortlisted ? 'Remove from shortlist' : 'Add to shortlist'}
            style={{ marginLeft: 'auto', padding: '5px 8px', borderRadius: 'var(--radius-btn)', border: '1.5px solid var(--border)', background: shortlisted ? 'var(--accent)' : 'transparent', color: shortlisted ? 'var(--accent-fg)' : 'var(--text3)', cursor: 'pointer', flexShrink: 0, display: 'flex', alignItems: 'center' }}
          >
            {shortlisted
              ? <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M5 3h14a1 1 0 0 1 1 1v18l-8-4-8 4V4a1 1 0 0 1 1-1z"/></svg>
              : <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 3h14a1 1 0 0 1 1 1v18l-8-4-8 4V4a1 1 0 0 1 1-1z"/></svg>
            }
          </button>
        )}
      </div>

    </article>
  )
}
