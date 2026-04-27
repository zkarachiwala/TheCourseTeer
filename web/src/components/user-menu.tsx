'use client'
import { useEffect, useRef, useState } from 'react'
import { useTheme } from 'next-themes'
import { useAuth } from '@/contexts/auth-context'
import Link from 'next/link'

const MODES = [
  { value: 'system', label: 'System', icon: '💻' },
  { value: 'light',  label: 'Light',  icon: '☀️' },
  { value: 'dark',   label: 'Dark',   icon: '🌙' },
] as const

export function UserMenu() {
  const { theme, setTheme } = useTheme()
  const { user, loading } = useAuth()
  const [open, setOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => setMounted(true), [])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    const onClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onClickOutside)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onClickOutside)
    }
  }, [open])

  return (
    <div ref={ref} style={{ position: 'relative', flexShrink: 0 }}>
      <button
        aria-label="Account menu"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen(v => !v)}
        style={{
          width: 34, height: 34,
          borderRadius: '50%',
          border: '1.5px solid var(--border)',
          background: open ? 'var(--bg3)' : 'var(--bg2)',
          cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text2)',
          transition: 'background 0.15s',
        }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          style={{
            position: 'absolute', right: 0, top: 'calc(100% + 8px)',
            width: 200,
            background: 'var(--card-bg)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-card)',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 300,
            overflow: 'hidden',
          }}
        >
          {!loading && user && (
            <div style={{ padding: '12px', borderBottom: '1px solid var(--border)' }}>
              <p style={{ fontSize: '13px', fontWeight: 600, margin: 0, color: 'var(--text)' }}>{user.userDetails}</p>
              <p style={{ fontSize: '11px', color: 'var(--text3)', margin: '2px 0 0' }}>{user.identityProvider}</p>
            </div>
          )}

          <div style={{ padding: '8px 12px 4px', fontSize: '11px', fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Display
          </div>
          {MODES.map(mode => (
            <button
              key={mode.value}
              role="menuitemradio"
              aria-checked={mounted && theme === mode.value}
              onClick={() => { setTheme(mode.value); setOpen(false) }}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                width: '100%', padding: '8px 12px',
                background: mounted && theme === mode.value ? 'var(--accent-soft)' : 'transparent',
                border: 'none', cursor: 'pointer',
                fontSize: '13px',
                color: mounted && theme === mode.value ? 'var(--accent)' : 'var(--text)',
                fontWeight: mounted && theme === mode.value ? 600 : 400,
                textAlign: 'left',
              }}
            >
              <span style={{ fontSize: '14px', width: 20, textAlign: 'center' }}>{mode.icon}</span>
              {mode.label}
              {mounted && theme === mode.value && (
                <span style={{ marginLeft: 'auto', fontSize: '12px' }}>✓</span>
              )}
            </button>
          ))}

          <div style={{ height: 1, background: 'var(--border)', margin: '4px 0' }} />

          {!loading && user ? (
            <Link
              href="/logout"
              role="menuitem"
              onClick={() => setOpen(false)}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                width: '100%', padding: '8px 12px 10px',
                background: 'transparent', border: 'none', cursor: 'pointer',
                fontSize: '13px', color: 'var(--text2)', textAlign: 'left',
                textDecoration: 'none'
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              Sign out
            </Link>
          ) : (
            <>
              <Link
                href="/login/github"
                role="menuitem"
                onClick={() => setOpen(false)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  width: '100%', padding: '8px 12px',
                  background: 'transparent', border: 'none', cursor: 'pointer',
                  fontSize: '13px', color: 'var(--text2)', textAlign: 'left',
                  textDecoration: 'none'
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                </svg>
                Sign in with GitHub
              </Link>
              <Link
                href="/login/microsoft"
                role="menuitem"
                onClick={() => setOpen(false)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  width: '100%', padding: '8px 12px 10px',
                  background: 'transparent', border: 'none', cursor: 'pointer',
                  fontSize: '13px', color: 'var(--text2)', textAlign: 'left',
                  textDecoration: 'none'
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <line x1="12" y1="3" x2="12" y2="21" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                </svg>
                Sign in with Microsoft
              </Link>
            </>
          )}
        </div>
      )}
    </div>
  )
}
