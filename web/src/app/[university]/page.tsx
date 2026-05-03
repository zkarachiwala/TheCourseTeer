export const dynamic = 'force-dynamic'

import {
  fetchCoursePage,
  fetchUniversities,
  fetchUniversityBySlug,
  parseSearchParams,
} from '../../lib/queries/courses'
import { CourseListClient } from '../../components/course-list-client'
import { notFound } from 'next/navigation'

interface Props {
  params: { university: string }
  searchParams: { [key: string]: string | string[] | undefined }
}

export default async function UniversityPage({ params, searchParams }: Props) {
  const { university: slug } = params
  const university = await fetchUniversityBySlug(slug)
  if (!university) notFound()

  const courseParams = parseSearchParams(searchParams, { slug })
  const [{ rows, total, availableDurations }, universities] = await Promise.all([
    fetchCoursePage(courseParams),
    fetchUniversities(),
  ])

  const featuredConfig = {
    universityName: university.name,
    tagline: `Explore undergraduate degrees at ${university.name}.`,
    highlight: university.scraperStatus === 'active' ? 'Verified Data' : 'Data Aggregated',
    ctaText: 'Visit University Site',
    ctaUrl: university.homepageUrl,
  }

  return (
    <CourseListClient
      courses={rows}
      total={total}
      availableDurations={availableDurations}
      universities={universities}
      currentParams={courseParams}
      featuredUni={featuredConfig}
    />
  )
}
