import Link from "next/link";
import Image from "next/image";
import { ThemeToggle } from "./theme-toggle";

export function Header() {
  return (
    <header className="border-b border-gray-200 dark:border-gray-700">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <Image src="/logo.png" alt="The Courseteer" height={32} width={32} className="h-8 w-auto" />
          <span className="text-lg font-semibold tracking-tight">The Courseteer</span>
        </Link>
        <nav className="flex items-center gap-4">
          <Link href="/courses" className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
            Courses
          </Link>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
