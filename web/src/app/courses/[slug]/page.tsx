export const dynamic = 'force-dynamic'
import { db } from '../../../../db'
import { courses, universities, courseCampuses, campuses } from '../../../../db/schema'
import { eq, sql, and } from 'drizzle-orm'
import { CourseListClient } from '@/components/course-list-client'
import { notFound } from 'next/navigation'

export default async function UniversityCoursesPage({ params }: { params: { slug: string } }) {
  const { slug } = params

  const [university] = await db
    .select()
    .from(universities)
    .where(eq(universities.slug, slug))
    .limit(1)

  if (!university) {
    notFound()
  }

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
      cc.atar_lowest_selection_rank as "atarSelectionRank",
      cp.name as "campusName"
    FROM courses c
    LEFT JOIN universities u ON c.university_id = u.id
    LEFT JOIN course_campuses cc ON c.id = cc.course_id
    LEFT JOIN campuses cp ON cc.campus_id = cp.id
    WHERE u.slug = ${slug}
    ORDER BY c.name ASC, u.name ASC, 
             COALESCE(cc.atar_lowest_selection_rank, cc.atar_guaranteed) DESC NULLS LAST
  `)

  const formattedCourses = distinctRows.map((row: any) => ({
    ...row,
    durationYears: row.durationYears != null ? Number(row.durationYears) : null,
    atarGuaranteed: row.atarGuaranteed != null ? Number(row.atarGuaranteed) : null,
    atarSelectionRank: row.atarSelectionRank != null ? Number(row.atarSelectionRank) : null,
  }))

  const uniList = await db
    .select({ slug: universities.slug, name: universities.name })
    .from(universities)
    .orderBy(sql`name ASC`)

  const featuredConfig = {
    universityName: university.name,
    tagline: `Explore undergraduate degrees at ${university.name}.`,
    highlight: university.scraperStatus === 'active' ? 'Verified Data' : 'Data Aggregated',
    ctaText: 'Visit University Site',
    ctaUrl: university.homepageUrl
  }

  return (
    <CourseListClient 
      courses={formattedCourses} 
      universities={uniList} 
      featuredUni={featuredConfig}
      initialUnis={[slug]}
    />
  )
}
