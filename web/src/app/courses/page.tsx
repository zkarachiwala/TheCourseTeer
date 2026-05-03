export const dynamic = 'force-dynamic'

import { db } from '../../../db'
import { universities } from '../../../db/schema'
import { asc, sql } from 'drizzle-orm'
import { CourseListClient } from '@/components/course-list-client'

export default async function CoursesPage() {
  // Fetch all course-campus combinations so users can see all options (e.g. multi-campus entries).
  const rows = await db.execute(sql`
    SELECT
      c.id || '-' || cp.id as id,
      c.name,
      c.faculty,
      c.degree_type as "degreeType",
      c.duration_years as "durationYears",
      c.source_url as "sourceUrl",
      u.name as "universityName",
      u.slug as "universitySlug",
      cc.atar_guaranteed as "atarGuaranteed",
      cc.atar_lowest_selection_rank as "atarSelectionRank",
      cp.name as "campusName"
    FROM courses c
    LEFT JOIN universities u ON c.university_id = u.id
    LEFT JOIN course_campuses cc ON c.id = cc.course_id
    LEFT JOIN campuses cp ON cc.campus_id = cp.id
    ORDER BY c.name ASC, u.name ASC, cp.name ASC
  `)

  // postgres-js returns a RowList which is an array of rows.
  // We map directly over it and ensure numeric types are correctly handled.
  const formattedCourses = (rows as any).map((row: any) => ({
    ...row,
    durationYears: row.durationYears != null ? Number(row.durationYears) : null,
    atarGuaranteed: row.atarGuaranteed != null ? Number(row.atarGuaranteed) : null,
    atarSelectionRank: row.atarSelectionRank != null ? Number(row.atarSelectionRank) : null,
  }))

  const uniList = await db
    .select({ slug: universities.slug, name: universities.name })
    .from(universities)
    .orderBy(asc(universities.name))

  return <CourseListClient courses={formattedCourses} universities={uniList} />
}
