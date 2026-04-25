'use client'
import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'
import { CourseCardData } from '@/components/course-card'

interface ShortlistCtx {
  shortlisted: CourseCardData[]
  isShortlisted: (id: string) => boolean
  toggle: (c: CourseCardData) => void
  remove: (id: string) => void
  drawerOpen: boolean
  openDrawer: () => void
  closeDrawer: () => void
}

const Ctx = createContext<ShortlistCtx | null>(null)

export function ShortlistProvider({ children }: { children: ReactNode }) {
  const [shortlisted, setShortlisted] = useState<CourseCardData[]>([])
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    try {
      const stored = localStorage.getItem('courseteer_shortlist')
      if (stored) setShortlisted(JSON.parse(stored))
    } catch {}
  }, [])

  function persist(items: CourseCardData[]) {
    setShortlisted(items)
    localStorage.setItem('courseteer_shortlist', JSON.stringify(items))
  }

  const isShortlisted = useCallback((id: string) => shortlisted.some(c => c.id === id), [shortlisted])

  const toggle = useCallback((c: CourseCardData) => {
    persist(shortlisted.some(x => x.id === c.id) ? shortlisted.filter(x => x.id !== c.id) : [...shortlisted, c])
  }, [shortlisted])

  const remove = useCallback((id: string) => persist(shortlisted.filter(c => c.id !== id)), [shortlisted])

  return (
    <Ctx.Provider value={{ shortlisted, isShortlisted, toggle, remove, drawerOpen, openDrawer: () => setDrawerOpen(true), closeDrawer: () => setDrawerOpen(false) }}>
      {children}
    </Ctx.Provider>
  )
}

export function useShortlist() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useShortlist must be inside ShortlistProvider')
  return ctx
}
