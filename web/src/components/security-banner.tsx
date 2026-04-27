'use client'
import { useAuth } from '@/contexts/auth-context'
import Link from 'next/link'

export function SecurityBanner() {
  const { user, loading } = useAuth()

  if (loading || user) return null

  return (
    <div className="bg-amber-50 dark:bg-amber-950/30 border-b border-amber-200 dark:border-amber-900 px-4 py-2">
      <div className="mx-auto max-w-6xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-200">
          <span className="text-lg">🛡️</span>
          <p>
            <span className="font-bold">ReadOnly / Demo Mode:</span> You are viewing public course data. 
            Sign in with GitHub to access protected features and admin tools.
          </p>
        </div>
        <Link
          href="/login"
          className="rounded-md bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-amber-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-600 transition-colors"
        >
          Sign in with GitHub
        </Link>
      </div>
    </div>
  )
}
