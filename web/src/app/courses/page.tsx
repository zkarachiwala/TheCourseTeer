export const dynamic = 'force-dynamic'

import { fetchCoursePage, fetchUniversities, parseSearchParams } from '@/lib/queries/courses'
import { CourseListClient } from '@/components/course-list-client'

export default async function CoursesPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined }
}) {
  const params = parseSearchParams(searchParams)
  const [{ rows, total, availableDurations }, universities] = await Promise.all([
    fetchCoursePage(params),
    fetchUniversities(),
  ])
  return (
    <CourseListClient
      courses={rows}
      total={total}
      availableDurations={availableDurations}
      universities={universities}
      currentParams={params}
    />
  )
}
