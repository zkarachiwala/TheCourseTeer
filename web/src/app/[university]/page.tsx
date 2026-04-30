export const dynamic = 'force-dynamic'

import { db } from '../../../db'
import { universities } from '../../../db/schema'
import { asc, sql, eq } from 'drizzle-orm'
import { CourseListClient } from '@/components/course-list-client'
import { notFound } from 'next/navigation'

interface Props {
  params: {
    university: string
  }
}

export default async function UniversityPage({ params }: Props) {
  const { university: slug } = params

  // Verify university exists
  const uni = await db.query.universities.findFirst({
    where: eq(universities.slug, slug),
  })

  if (!uni) {
    notFound()
  }

  // Use DISTINCT ON to get exactly one row per course for this university
  const distinctRows = await db.execute(sql`
    SELECT DISTINCT ON (c.name)
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
    WHERE u.slug = ${slug}
    ORDER BY c.name ASC, cc.atar_guaranteed DESC NULLS LAST
  `)

  const formattedCourses = distinctRows.map((row: any) => ({
    ...row,
    durationYears: row.durationYears != null ? Number(row.durationYears) : null,
    atarGuaranteed: row.atarGuaranteed != null ? Number(row.atarGuaranteed) : null,
  }))

  const uniList = await db
    .select({ slug: universities.slug, name: universities.name })
    .from(universities)
    .orderBy(asc(universities.name))

  return (
    <CourseListClient 
      courses={formattedCourses} 
      universities={uniList} 
      initialUnis={[slug]}
    />
  )
}
