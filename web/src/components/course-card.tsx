import { getArea, getMonogram, atarColor, AREAS } from '@/lib/area-map'

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
}

export function CourseCard({ course, onClick, selected, onShortlist, shortlisted }: Props) {
  const areaKey = getArea(course.faculty)
  const area = areaKey ? AREAS[areaKey] : null

  return (
    <article onClick={onClick} style={{ background: 'var(--card-bg)', borderRadius: 'var(--radius-card)', border: `1.5px solid ${selected ? 'var(--accent)' : 'var(--border)'}`, padding: '20px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '10px', boxShadow: selected ? 'var(--shadow-lg)' : 'var(--shadow)', transition: 'all 0.2s' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', minHeight: '22px' }}>
        {area && <span style={{ background: area.color, color: '#fff', fontSize: '11px', fontWeight: 600, padding: '2px 10px', borderRadius: 'var(--radius-pill)', flexShrink: 0 }}>{area.label}</span>}
        {course.atarGuaranteed != null && <span style={{ fontSize: '13px', fontWeight: 700, color: atarColor(course.atarGuaranteed), flexShrink: 0, marginLeft: 'auto' }}>ATAR {course.atarGuaranteed}</span>}
      </div>
      <h3 style={{ fontFamily: 'Manrope, sans-serif', fontWeight: 700, fontSize: '15px', color: 'var(--text)', lineHeight: 1.3, margin: 0, flex: 1 }}>{course.name}</h3>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{ width: 32, height: 32, borderRadius: '8px', background: 'var(--accent-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '11px', color: 'var(--accent)', flexShrink: 0 }}>{getMonogram(course.universityName)}</span>
        <div>
          <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text2)', margin: 0 }}>{course.universityName}</p>
          {course.campusName && <p style={{ fontSize: '12px', color: 'var(--text3)', margin: 0 }}>📍 {course.campusName}</p>}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minHeight: '26px' }}>
        {course.durationYears != null && <p style={{ fontSize: '12px', color: 'var(--text3)', margin: 0 }}>{course.durationYears} years · {course.degreeType}</p>}
        {onShortlist && (
          <button onClick={e => { e.stopPropagation(); onShortlist() }} style={{ marginLeft: 'auto', padding: '5px 10px', borderRadius: 'var(--radius-btn)', border: '1.5px solid var(--border)', background: shortlisted ? 'var(--accent)' : 'transparent', color: shortlisted ? 'var(--accent-fg)' : 'var(--text2)', cursor: 'pointer', fontSize: '11px', fontWeight: 600, flexShrink: 0 }}>
            {shortlisted ? '✓ Saved' : '+ Save'}
          </button>
        )}
      </div>
    </article>
  )
}
