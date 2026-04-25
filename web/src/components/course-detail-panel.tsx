'use client'
import { useEffect } from 'react'
import { CourseCardData } from './course-card'
import { getArea, atarColor, AREAS } from '@/lib/area-map'

interface Props { course: CourseCardData; onClose: () => void }

export function CourseDetailPanel({ course, onClose }: Props) {
  const areaKey = getArea(course.faculty)
  const area = areaKey ? AREAS[areaKey] : null

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])

  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'oklch(0% 0 0 / 0.5)', zIndex: 200, backdropFilter: 'blur(4px)' }} />
      <aside style={{ position: 'fixed', right: 0, top: 0, bottom: 0, width: 'min(480px, 100vw)', background: 'var(--bg2)', borderLeft: '1px solid var(--border)', zIndex: 201, display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)', animation: 'slideIn 0.3s cubic-bezier(0.16,1,0.3,1)' }}>
        <style>{`@keyframes slideIn{from{transform:translateX(100%)}to{transform:translateX(0)}}`}</style>

        <div style={{ padding: '20px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            {area && <span style={{ background: area.color, color: '#fff', fontSize: '11px', fontWeight: 600, padding: '2px 10px', borderRadius: 'var(--radius-pill)' }}>{area.label}</span>}
            <h2 style={{ fontFamily: 'Manrope, sans-serif', fontWeight: 800, fontSize: '19px', color: 'var(--text)', margin: '8px 0 4px', lineHeight: 1.2 }}>{course.name}</h2>
            <p style={{ fontSize: '14px', color: 'var(--text2)', margin: 0 }}>{course.universityName}</p>
          </div>
          <button aria-label="Close panel" onClick={onClose} style={{ background: 'var(--bg3)', border: 'none', borderRadius: '8px', width: 32, height: 32, cursor: 'pointer', color: 'var(--text2)', fontSize: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>×</button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <Stat label="ATAR" value={course.atarGuaranteed != null ? String(course.atarGuaranteed) : 'N/A'} valueColor={course.atarGuaranteed != null ? atarColor(course.atarGuaranteed) : undefined} />
            <Stat label="Duration" value={course.durationYears != null ? `${course.durationYears} years` : 'N/A'} />
            <Stat label="Type" value={course.degreeType ?? 'N/A'} />
            <Stat label="Campus" value={course.campusName ?? 'N/A'} />
          </div>
        </div>

        {course.sourceUrl && (
          <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)' }}>
            <a href={course.sourceUrl} target="_blank" rel="noopener noreferrer" style={{ display: 'block', textAlign: 'center', padding: '13px', background: 'var(--accent)', color: 'var(--accent-fg)', borderRadius: 'var(--radius-btn)', fontWeight: 600, fontSize: '14px', textDecoration: 'none' }}>
              View on University Website →
            </a>
          </div>
        )}
      </aside>
    </>
  )
}

function Stat({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={{ background: 'var(--bg3)', borderRadius: '12px', padding: '14px', textAlign: 'center' }}>
      <p style={{ fontSize: '11px', color: 'var(--text3)', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</p>
      <p style={{ fontSize: '20px', fontWeight: 700, color: valueColor ?? 'var(--text)', margin: 0, fontFamily: 'Manrope, sans-serif' }}>{value}</p>
    </div>
  )
}
