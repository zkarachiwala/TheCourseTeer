'use client'
import { useState } from 'react'
import { CourseCardData } from './course-card'

interface Props {
  courses: CourseCardData[]
  onClose: () => void
  onRemove: (id: string) => void
}

export function ShortlistDrawer({ courses, onClose, onRemove }: Props) {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSend() {
    if (!email || courses.length === 0) return
    setBusy(true)
    setError(null)
    try {
      const res = await fetch('/api/shortlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, courseIds: courses.map(c => c.id) }),
      })
      if (res.status === 401) {
        setError('Please sign in to send your shortlist.')
        return
      }
      if (!res.ok) throw new Error('Failed to send')
      setSent(true)
    } catch (e) {
      setError('Something went wrong. Please try again later.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'oklch(0% 0 0 / 0.4)', zIndex: 200 }} />
      <aside style={{ position: 'fixed', right: 0, top: 0, bottom: 0, width: 'min(420px, 100vw)', background: 'var(--bg2)', borderLeft: '1px solid var(--border)', zIndex: 201, display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontFamily: 'Manrope, sans-serif', fontWeight: 700, fontSize: '17px', color: 'var(--text)', margin: 0 }}>
            Shortlist{' '}
            <span style={{ background: 'var(--accent)', color: 'var(--accent-fg)', borderRadius: 'var(--radius-pill)', fontSize: '12px', padding: '2px 8px', marginLeft: 6 }}>{courses.length}</span>
          </h2>
          <button onClick={onClose} aria-label="Close shortlist" style={{ background: 'var(--bg3)', border: 'none', borderRadius: '8px', width: 32, height: 32, cursor: 'pointer', color: 'var(--text2)', fontSize: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>×</button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
          {courses.length === 0 ? (
            <p style={{ textAlign: 'center', color: 'var(--text3)', marginTop: 48, fontSize: '14px' }}>No courses saved yet</p>
          ) : (
            courses.map(c => (
              <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'var(--card-bg)', borderRadius: '12px', marginBottom: '8px', border: '1px solid var(--border)' }}>
                <div>
                  <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', margin: '0 0 2px' }}>{c.name}</p>
                  <p style={{ fontSize: '12px', color: 'var(--text2)', margin: 0 }}>{c.universityName}</p>
                </div>
                <button onClick={() => onRemove(c.id)} aria-label={`Remove ${c.name}`} style={{ background: 'transparent', border: 'none', color: 'var(--text3)', cursor: 'pointer', fontSize: '18px', padding: '4px' }}>×</button>
              </div>
            ))
          )}
        </div>

        <div style={{ padding: '16px', borderTop: '1px solid var(--border)' }}>
          {error && (
            <p style={{ fontSize: '12px', color: 'var(--error, #ef4444)', marginBottom: '8px', textAlign: 'center' }}>{error}</p>
          )}
          {sent ? (
            <p style={{ textAlign: 'center', color: 'var(--accent)', fontWeight: 600, fontSize: '14px' }}>✓ Shortlist sent to {email}</p>
          ) : (
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="email" placeholder="your@email.com" value={email}
                onChange={e => { setEmail(e.target.value); setError(null); }}
                style={{ flex: 1, padding: '10px 14px', borderRadius: 'var(--radius-btn)', border: '1.5px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)', fontSize: '14px', outline: 'none' }}
              />
              <button onClick={handleSend} disabled={busy || courses.length === 0}
                style={{ padding: '10px 18px', background: 'var(--accent)', color: 'var(--accent-fg)', border: 'none', borderRadius: 'var(--radius-btn)', fontWeight: 600, fontSize: '14px', cursor: 'pointer', opacity: busy ? 0.7 : 1 }}>
                {busy ? '…' : 'Send →'}
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  )
}
