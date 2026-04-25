export const dynamic = 'force-dynamic'

import { db } from '../../../db'
import { courses, universities, courseCampuses, campuses } from '../../../db/schema'
import { eq, asc } from 'drizzle-orm'
import { CourseListClient } from '@/components/course-list-client'
import type { CourseCardData } from '@/components/course-card'

export default async function CoursesPage() {
  const rows = await db
    .select({
      id: courses.id,
      name: courses.name,
      faculty: courses.faculty,
      degreeType: courses.degreeType,
      durationYears: courses.durationYears,
      sourceUrl: courses.sourceUrl,
      universityName: universities.name,
      universitySlug: universities.slug,
      atarGuaranteed: courseCampuses.atarGuaranteed,
      campusName: campuses.name,
    })
    .from(courses)
    .leftJoin(universities, eq(courses.universityId, universities.id))
    .leftJoin(courseCampuses, eq(courses.id, courseCampuses.courseId))
    .leftJoin(campuses, eq(courseCampuses.campusId, campuses.id))
    .orderBy(asc(courses.name))

  // Deduplicate by course — keep the row with the highest guaranteed ATAR (most selective campus)
  const map = new Map<string, CourseCardData>()
  for (const row of rows) {
    const prev = map.get(row.id)
    const isFirstOrBetter = !prev || (row.atarGuaranteed != null && (prev.atarGuaranteed == null || row.atarGuaranteed > prev.atarGuaranteed))
    if (isFirstOrBetter) {
      map.set(row.id, {
        id: row.id,
        name: row.name,
        faculty: row.faculty,
        degreeType: row.degreeType,
        durationYears: row.durationYears != null ? Number(row.durationYears) : null,
        sourceUrl: row.sourceUrl,
        universityName: row.universityName ?? '',
        universitySlug: row.universitySlug ?? '',
        atarGuaranteed: row.atarGuaranteed,
        campusName: row.campusName,
      })
    }
  }

  const uniList = await db
    .select({ slug: universities.slug, name: universities.name })
    .from(universities)
    .orderBy(asc(universities.name))

  return <CourseListClient courses={[...map.values()]} universities={uniList} />
}
