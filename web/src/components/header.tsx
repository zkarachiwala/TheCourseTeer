'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ThemeToggle } from './theme-toggle'

export function Header() {
  const pathname = usePathname()
  return (
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
      <nav style={{ display: 'flex', gap: '4px', flex: 1 }}>
        <NavLink href="/courses" active={pathname.startsWith('/courses')}>Courses</NavLink>
        <NavLink href="/admin" active={pathname.startsWith('/admin')}>Admin</NavLink>
      </nav>
      <ThemeToggle />
    </header>
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
