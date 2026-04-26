import { CourseCardData } from './course-card'
import { getArea, getMonogram, atarColor, degreeLabel, AREAS } from '@/lib/area-map'

interface Props { course: CourseCardData; onClick: () => void; selected?: boolean }

export function CourseRow({ course, onClick, selected }: Props) {
  const areaKey = getArea(course.faculty)
  const area = areaKey ? AREAS[areaKey] : null

  return (
    <div onClick={onClick} style={{ display: 'grid', gridTemplateColumns: '44px 1fr 60px 60px 24px', alignItems: 'center', gap: '16px', padding: '14px var(--px)', background: selected ? 'var(--accent-soft)' : 'transparent', borderBottom: '1px solid var(--border)', cursor: 'pointer', transition: 'background 0.15s' }}>
      <span style={{ width: 36, height: 36, borderRadius: '8px', background: 'var(--bg3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '11px', color: 'var(--text2)' }}>{getMonogram(course.universityName)}</span>
      <div>
        <p style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text)', margin: '0 0 2px' }}>{course.name}</p>
        <p style={{ fontSize: '12px', color: 'var(--text2)', margin: 0 }}>
          {course.universityName}
          {course.campusName && ` · ${course.campusName}`}
          {area && <span style={{ marginLeft: 8, background: area.color, color: '#fff', fontSize: '10px', padding: '1px 7px', borderRadius: 'var(--radius-pill)' }}>{area.label}</span>}
        </p>
      </div>
      <span style={{ fontSize: '13px', color: 'var(--text3)', textAlign: 'right' }}>{course.durationYears != null ? `${course.durationYears} ${course.durationYears === 1 ? 'yr' : 'yrs'}` : '—'}</span>
      <span style={{ fontSize: '13px', fontWeight: 700, color: course.atarGuaranteed != null ? atarColor(course.atarGuaranteed) : 'var(--text3)', textAlign: 'right' }}>{course.atarGuaranteed ?? '—'}</span>
      <span style={{ color: 'var(--text3)', fontSize: '18px', textAlign: 'right' }}>›</span>
    </div>
  )
}
