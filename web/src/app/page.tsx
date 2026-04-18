import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center gap-6 py-16 text-center">
      <h1 className="text-4xl font-bold tracking-tight">Find your course</h1>
      <p className="max-w-md text-gray-600 dark:text-gray-400">
        Browse undergraduate courses from Victorian universities* in one place.
      </p>
      <p className="text-xs text-gray-400 dark:text-gray-500">
        * All Australian universities coming soon
      </p>
      <Link
        href="/courses"
        className="rounded bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-700 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-300"
      >
        Browse courses
      </Link>
    </div>
  );
}
