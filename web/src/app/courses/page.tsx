export const dynamic = 'force-dynamic'

import { db } from '../../../db'
import { courses, universities, courseCampuses, campuses } from '../../../db/schema'
import { eq, asc, desc, sql } from 'drizzle-orm'
import { CourseListClient } from '@/components/course-list-client'

export default async function CoursesPage() {
  // Use a raw subquery or distinct on to get the best campus for each course at the DB level
  // Drizzle's DISTINCT ON is best achieved via sql template for complex join priorities
  const distinctRows = await db.execute(sql`
    SELECT DISTINCT ON (c.name, u.name)
      c.id,
      c.name,
      c.faculty,
      c.degree_type as "degreeType",
      c.duration_years as "durationYears",
      c.source_url as "sourceUrl",
      u.name as "universityName",
      u.slug as "universitySlug",
      cc.atar_guaranteed as "atarGuaranteed",
      cp.name as "campusName"
    FROM courses c
    LEFT JOIN universities u ON c.university_id = u.id
    LEFT JOIN course_campuses cc ON c.id = cc.course_id
    LEFT JOIN campuses cp ON cc.campus_id = cp.id
    ORDER BY c.name ASC, u.name ASC, cc.atar_guaranteed DESC NULLS LAST
  `)

  const formattedCourses = distinctRows.rows.map((row: any) => ({
    ...row,
    durationYears: row.durationYears != null ? Number(row.durationYears) : null,
  }))

  const uniList = await db
    .select({ slug: universities.slug, name: universities.name })
    .from(universities)
    .orderBy(asc(universities.name))

  return <CourseListClient courses={formattedCourses} universities={uniList} />
}
