import Link from "next/link";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <nav className="mb-6 flex gap-4 border-b border-gray-200 pb-3 text-sm dark:border-gray-700">
        <Link
          href="/admin/health"
          className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
        >
          Health
        </Link>
        <Link
          href="/admin/atar-issues"
          className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
        >
          ATAR Issues
        </Link>
      </nav>
      {children}
    </div>
  );
}
