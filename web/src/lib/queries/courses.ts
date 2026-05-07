import { db } from '../../../db'
import { sql, asc, eq, SQL } from 'drizzle-orm'
import { universities } from '../../../db/schema'
import type { CourseCardData } from '@/components/course-card'

export interface CourseFilters {
  search?: string
  areas?: string[]
  unis?: string[]
  durations?: string[]
  minAtar?: number
}

export interface FetchCoursePageParams {
  slug?: string
  page: number
  pageSize: number
  filters: CourseFilters
}

export interface FetchCoursePageResult {
  rows: CourseCardData[]
  total: number
  availableDurations: number[]
}

// Patterns extracted from FACULTY_MAP in area-map.ts for SQL regex matching
const FACULTY_PATTERNS: Record<string, string> = {
  engineering: 'engineering|electrical|civil|mechanical|chemical',
  technology: 'information technology|computer science|software|cybersecurity|data science',
  business: 'business|commerce|economics|management|accounting|finance|marketing',
  medicine: 'medicine|medical|nursing|pharmacy|dentist|dental',
  law: 'law|legal',
  science: 'science|chemistry|physics|biology|mathematics|environmental',
  health: 'health|physiotherapy|nutrition|rehabilitation|allied health',
  education: 'education|teaching',
  design: 'design|architecture|fashion|visual|media arts',
  arts: 'arts|humanities|history|philosophy|languages|literature|music|creative',
  sport: 'sport|kinesiology|exercise',
}

function toArray(val: string | string[] | undefined): string[] | undefined {
  if (!val) return undefined
  if (typeof val === 'string') {
    const trimmed = val.trim()
    if (!trimmed) return undefined
    const parts = trimmed.split(',').map(s => s.trim()).filter(Boolean)
    return parts.length > 0 ? parts : undefined
  }
  if (Array.isArray(val)) {
    const filtered = val.filter(s => typeof s === 'string' && s.trim())
    return filtered.length > 0 ? filtered : undefined
  }
  return undefined
}

export function parseSearchParams(
  raw: { [key: string]: string | string[] | undefined },
  opts?: { slug?: string }
): FetchCoursePageParams {
  const page = Math.max(1, parseInt(String(raw.page ?? '1'), 10) || 1)
  const pageSizeRaw = parseInt(String(raw.pageSize ?? '48'), 10)
  const pageSize = [24, 48, 72, 96].includes(pageSizeRaw) ? pageSizeRaw : 48

  const search =
    typeof raw.search === 'string' && raw.search.trim()
      ? raw.search.trim()
      : undefined

  const minAtarRaw = Number(raw.minAtar)
  const minAtar =
    raw.minAtar && !isNaN(minAtarRaw) && minAtarRaw > 0 ? minAtarRaw : undefined

  const filters: CourseFilters = {}
  if (search) filters.search = search
  const areas = toArray(raw.areas)
  if (areas) filters.areas = areas
  const unis = toArray(raw.unis)
  if (unis) filters.unis = unis
  const durations = toArray(raw.durations)
  if (durations) filters.durations = durations
  if (minAtar) filters.minAtar = minAtar

  return { slug: opts?.slug, page, pageSize, filters }
}

export async function fetchCoursePage(
  params: FetchCoursePageParams
): Promise<FetchCoursePageResult> {
  const { slug, page, pageSize, filters } = params
  const whereParts: SQL[] = []

  if (slug) {
    whereParts.push(sql`u.slug = ${slug}`)
  }

  if (filters.search) {
    const q = `%${filters.search}%`
    whereParts.push(sql`(c.name ILIKE ${q} OR u.name ILIKE ${q})`)
  }

  if (filters.areas?.length) {
    const areaParts = filters.areas
      .map(area => {
        const pattern = FACULTY_PATTERNS[area]
        if (!pattern) return null
        return sql`(c.faculty ~* ${pattern} OR c.name ~* ${pattern})`
      })
      .filter((p): p is SQL => p !== null)

    if (areaParts.length > 0) {
      const areaClause = areaParts.reduce((acc, p) => sql`${acc} OR ${p}`)
      whereParts.push(sql`(${areaClause})`)
    }
  }

  if (filters.unis?.length) {
    const vals = sql.join(filters.unis.map(s => sql`${s}`), sql.raw(', '))
    whereParts.push(sql`u.slug IN (${vals})`)
  }

  if (filters.durations?.length) {
    const nums = filters.durations.map(Number).filter(n => !isNaN(n))
    if (nums.length > 0) {
      const vals = sql.join(nums.map(n => sql`${n}`), sql.raw(', '))
      whereParts.push(sql`c.duration_years IN (${vals})`)
    }
  }

  if (filters.minAtar != null) {
    whereParts.push(
      sql`COALESCE(cc.atar_lowest_selection_rank, cc.atar_guaranteed) >= ${filters.minAtar}`
    )
  }

  const whereClause =
    whereParts.length > 0
      ? sql`WHERE ${whereParts.reduce((acc, p) => sql`${acc} AND ${p}`)}`
      : sql``

  const offset = (page - 1) * pageSize

  const [dataRows, countRows, durationRows] = await Promise.all([
    db.execute(sql`
      SELECT
        c.id::text || '-' || COALESCE(cp.id::text, 'none') AS id,
        c.name,
        c.faculty,
        c.degree_type AS "degreeType",
        c.duration_years AS "durationYears",
        c.source_url AS "sourceUrl",
        u.name AS "universityName",
        u.slug AS "universitySlug",
        cc.atar_guaranteed AS "atarGuaranteed",
        cc.atar_lowest_selection_rank AS "atarSelectionRank",
        cp.name AS "campusName"
      FROM courses c
      LEFT JOIN universities u ON c.university_id = u.id
      LEFT JOIN course_campuses cc ON c.id = cc.course_id
      LEFT JOIN campuses cp ON cc.campus_id = cp.id
      ${whereClause}
      ORDER BY c.name ASC, u.name ASC, cp.name ASC
      LIMIT ${pageSize} OFFSET ${offset}
    `),
    db.execute(sql`
      SELECT COUNT(*) AS count
      FROM courses c
      LEFT JOIN universities u ON c.university_id = u.id
      LEFT JOIN course_campuses cc ON c.id = cc.course_id
      LEFT JOIN campuses cp ON cc.campus_id = cp.id
      ${whereClause}
    `),
    db.execute(sql`
      SELECT DISTINCT c.duration_years AS "durationYears"
      FROM courses c
      LEFT JOIN universities u ON c.university_id = u.id
      ${slug ? sql`WHERE u.slug = ${slug}` : sql``}
      ORDER BY 1
    `),
  ])

  const rows = (dataRows as any[]).map(row => ({
    ...row,
    durationYears: row.durationYears != null ? Number(row.durationYears) : null,
    atarGuaranteed: row.atarGuaranteed != null ? Number(row.atarGuaranteed) : null,
    atarSelectionRank:
      row.atarSelectionRank != null ? Number(row.atarSelectionRank) : null,
  })) as CourseCardData[]

  const total = Number((countRows as any)[0]?.count ?? 0)

  const availableDurations = (durationRows as any[])
    .map(r => Number(r.durationYears))
    .filter(n => !isNaN(n))

  return { rows, total, availableDurations }
}

export async function fetchUniversities(): Promise<{ slug: string; name: string }[]> {
  return db
    .select({ slug: universities.slug, name: universities.name })
    .from(universities)
    .orderBy(asc(universities.name))
}

export async function fetchUniversityBySlug(slug: string) {
  const [university] = await db
    .select()
    .from(universities)
    .where(eq(universities.slug, slug))
    .limit(1)
  return university
}
