'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { UserMenu } from './user-menu'
import { useShortlist } from '@/contexts/shortlist-context'
import { ShortlistDrawer } from './shortlist-drawer'

export function Header() {
  const pathname = usePathname()
  const { shortlisted, openDrawer, drawerOpen, closeDrawer, remove } = useShortlist()

  return (
    <>
      <header style={{
        position: 'sticky', top: 0, zIndex: 100,
        height: 'var(--header-h)',
        background: 'color-mix(in oklch, var(--bg) 85%, transparent)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center',
        padding: '0 var(--px)', gap: '16px',
      }}>
        <Link href="/" style={{ fontFamily: 'Manrope, sans-serif', fontWeight: 800, fontSize: '18px', color: 'var(--text)', textDecoration: 'none', flexShrink: 0 }}>
          Courseteer
        </Link>
        <nav style={{ display: 'flex', gap: '4px', flex: 1, alignItems: 'center' }}>
          <NavLink href="/courses" active={pathname.startsWith('/courses')}>Courses</NavLink>
          <NavLink href="/admin" active={pathname.startsWith('/admin')}>Admin</NavLink>
        </nav>
        {shortlisted.length > 0 && (
          <button onClick={openDrawer} style={{ padding: '6px 14px', borderRadius: 'var(--radius-pill)', border: 'none', cursor: 'pointer', fontSize: '14px', fontWeight: 500, background: 'var(--bg3)', color: 'var(--text2)', display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
            📋
            <span style={{ background: 'var(--accent)', color: 'var(--accent-fg)', borderRadius: 'var(--radius-pill)', fontSize: '11px', padding: '1px 6px', fontWeight: 700 }}>{shortlisted.length}</span>
          </button>
        )}
        <UserMenu />
      </header>
      {drawerOpen && <ShortlistDrawer courses={shortlisted} onClose={closeDrawer} onRemove={remove} />}
    </>
  )
}

function NavLink({ href, children, active }: { href: string; children: React.ReactNode; active: boolean }) {
  return (
    <Link href={href} style={{
      padding: '6px 14px',
      borderRadius: 'var(--radius-pill)',
      fontSize: '14px', fontWeight: 500,
      color: active ? 'var(--accent-fg)' : 'var(--text2)',
      background: active ? 'var(--accent)' : 'transparent',
      textDecoration: 'none',
      transition: 'all 0.2s',
    }}>
      {children}
    </Link>
  )
}
