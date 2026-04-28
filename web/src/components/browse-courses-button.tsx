"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";

export function BrowseCoursesButton() {
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  const handleClick = () => {
    startTransition(() => {
      router.push("/courses");
    });
  };

  return (
    <button
      onClick={handleClick}
      disabled={isPending}
      className="inline-flex items-center gap-2 rounded bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-70 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-300"
    >
      {isPending && (
        <svg
          className="h-4 w-4 animate-spin text-white dark:text-gray-900"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      )}
      {isPending ? "Loading courses..." : "Browse courses"}
    </button>
  );
}
