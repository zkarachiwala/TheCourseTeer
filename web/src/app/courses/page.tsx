export const dynamic = "force-dynamic";

import { db } from "../../../db";
import { courses, universities, courseCampuses, campuses } from "../../../db/schema";
import { eq, asc, desc, sql, and, ilike, gte, isNotNull } from "drizzle-orm";
import Link from "next/link";
import { FilterRow, type Filters } from "@/components/course-filter-row";

const PAGE_SIZE = 25;

type SortCol = "name" | "university" | "type" | "duration" | "campus";
type SortDir = "asc" | "desc";

const SORT_COLUMNS = {
  name: courses.name,
  university: universities.name,
  type: courses.degreeType,
  duration: courses.durationYears,
  campus: campuses.name,
} as const;

const DEGREE_LABELS: Record<string, string> = {
  UG: "Undergraduate",
  PG: "Postgraduate",
};

type CourseRow = {
  id: string;
  name: string;
  sourceUrl: string | null;
  degreeType: string;
  durationYears: string | null;
  universityName: string;
  campusName: string | null;
  atarGuaranteed: number | null;
};

function buildWhere(f: Filters) {
  const conds = [];
  if (f.name) conds.push(ilike(courses.name, `%${f.name}%`));
  if (f.university) conds.push(eq(universities.name, f.university));
  if (f.type) conds.push(eq(courses.degreeType, f.type));
  if (f.duration) conds.push(eq(courses.durationYears, f.duration));
  if (f.campus) conds.push(eq(campuses.name, f.campus));
  if (f.atarMin) conds.push(gte(courseCampuses.atarGuaranteed, parseInt(f.atarMin, 10)));
  return conds.length > 0 ? and(...conds) : undefined;
}

async function getCourses(sort: SortCol, dir: SortDir, page: number, filters: Filters) {
  const order = dir === "asc" ? asc(SORT_COLUMNS[sort]) : desc(SORT_COLUMNS[sort]);
  const where = buildWhere(filters);

  const [rows, [{ total }]] = await Promise.all([
    db
      .select({
        id: courses.id,
        name: courses.name,
        sourceUrl: courses.sourceUrl,
        degreeType: courses.degreeType,
        durationYears: courses.durationYears,
        universityName: universities.name,
        campusName: campuses.name,
        atarGuaranteed: courseCampuses.atarGuaranteed,
      })
      .from(courses)
      .innerJoin(universities, eq(courses.universityId, universities.id))
      .leftJoin(courseCampuses, eq(courseCampuses.courseId, courses.id))
      .leftJoin(campuses, eq(courseCampuses.campusId, campuses.id))
      .where(where)
      .orderBy(order)
      .limit(PAGE_SIZE)
      .offset((page - 1) * PAGE_SIZE),
    db
      .select({ total: sql<number>`count(*)` })
      .from(courses)
      .innerJoin(universities, eq(courses.universityId, universities.id))
      .leftJoin(courseCampuses, eq(courseCampuses.courseId, courses.id))
      .leftJoin(campuses, eq(courseCampuses.campusId, campuses.id))
      .where(where),
  ]);

  return { rows: rows as CourseRow[], total: Number(total) };
}

async function getFilterOptions() {
  const [uniRows, durRows, camRows] = await Promise.all([
    db.selectDistinct({ name: universities.name }).from(universities).orderBy(asc(universities.name)),
    db.selectDistinct({ dur: courses.durationYears }).from(courses).where(isNotNull(courses.durationYears)).orderBy(asc(courses.durationYears)),
    db
      .selectDistinct({ name: campuses.name, university: universities.name })
      .from(campuses)
      .innerJoin(universities, eq(campuses.universityId, universities.id))
      .orderBy(asc(campuses.name)),
  ]);
  return {
    universities: uniRows.map(r => r.name),
    durations: durRows.map(r => r.dur!),
    campuses: camRows as { name: string; university: string }[],
  };
}

function colUrl(col: SortCol, current: SortCol, dir: SortDir, filters: Filters) {
  const nextDir = col === current && dir === "asc" ? "desc" : "asc";
  const p = new URLSearchParams({ sort: col, dir: nextDir, page: "1" });
  if (filters.name) p.set("f_name", filters.name);
  if (filters.university) p.set("f_uni", filters.university);
  if (filters.type) p.set("f_type", filters.type);
  if (filters.duration) p.set("f_dur", filters.duration);
  if (filters.campus) p.set("f_cam", filters.campus);
  if (filters.atarMin) p.set("f_atar_min", filters.atarMin);
  return `/courses?${p.toString()}`;
}

function SortHeader({ col, label, current, dir, filters, className }: { col: SortCol; label: string; current: SortCol; dir: SortDir; filters: Filters; className?: string }) {
  const active = col === current;
  const indicator = active ? (dir === "asc" ? " ↑" : " ↓") : "";
  return (
    <th className={`pb-2 pr-4 text-left font-medium ${className ?? ""}`}>
      <Link href={colUrl(col, current, dir, filters)} className={active ? "underline underline-offset-2" : "hover:underline hover:underline-offset-2"}>
        {label}{indicator}
      </Link>
    </th>
  );
}

function Pagination({ page, total, sort, dir, filters }: { page: number; total: number; sort: SortCol; dir: SortDir; filters: Filters }) {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  if (totalPages <= 1) return null;
  const base = new URLSearchParams({ sort, dir });
  if (filters.name) base.set("f_name", filters.name);
  if (filters.university) base.set("f_uni", filters.university);
  if (filters.type) base.set("f_type", filters.type);
  if (filters.duration) base.set("f_dur", filters.duration);
  if (filters.campus) base.set("f_cam", filters.campus);
  if (filters.atarMin) base.set("f_atar_min", filters.atarMin);
  const href = (p: number) => `/courses?${base.toString()}&page=${p}`;
  return (
    <div className="mt-6 flex items-center justify-between text-sm">
      <span className="text-gray-500 dark:text-gray-400">Page {page} of {totalPages}</span>
      <div className="flex gap-2">
        {page > 1 && (
          <Link href={href(page - 1)} className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800">
            Previous
          </Link>
        )}
        {page < totalPages && (
          <Link href={href(page + 1)} className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800">
            Next
          </Link>
        )}
      </div>
    </div>
  );
}

const VALID_SORTS: SortCol[] = ["name", "university", "type", "duration", "campus"];

export default async function CoursesPage({
  searchParams,
}: {
  searchParams: { sort?: string; dir?: string; page?: string; f_name?: string; f_uni?: string; f_type?: string; f_dur?: string; f_cam?: string; f_atar_min?: string };
}) {
  const sort = (VALID_SORTS.includes(searchParams.sort as SortCol) ? searchParams.sort : "name") as SortCol;
  const dir: SortDir = searchParams.dir === "desc" ? "desc" : "asc";
  const page = Math.max(1, parseInt(searchParams.page ?? "1", 10) || 1);

  const filters: Filters = {
    name: searchParams.f_name ?? "",
    university: searchParams.f_uni ?? "",
    type: searchParams.f_type ?? "",
    duration: searchParams.f_dur ?? "",
    campus: searchParams.f_cam ?? "",
    atarMin: searchParams.f_atar_min ?? "",
  };

  const [{ rows: courseList, total }, filterOptions] = await Promise.all([
    getCourses(sort, dir, page, filters),
    getFilterOptions(),
  ]);

  const start = (page - 1) * PAGE_SIZE + 1;
  const end = Math.min(page * PAGE_SIZE, total);

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Courses</h1>
      <p className="mb-4 text-sm text-gray-500">
        {total > 0 ? `Showing ${start}–${end} of ${total} rows` : "No courses found"}
      </p>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <SortHeader col="name" label="Course" current={sort} dir={dir} filters={filters} />
              <SortHeader col="university" label="University" current={sort} dir={dir} filters={filters} />
              <SortHeader col="type" label="Type" current={sort} dir={dir} filters={filters} />
              <th className="pb-2 pr-4 text-left font-medium">ATAR</th>
              <SortHeader col="duration" label="Duration" current={sort} dir={dir} filters={filters} className="hidden sm:table-cell" />
              <SortHeader col="campus" label="Campus" current={sort} dir={dir} filters={filters} />
            </tr>
            <FilterRow
              universities={filterOptions.universities}
              durations={filterOptions.durations}
              campuses={filterOptions.campuses}
              sort={sort}
              dir={dir}
              filters={filters}
            />
          </thead>
          <tbody>
            {courseList.map((course, i) => (
              <tr key={`${course.id}-${i}`} className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-2 pr-4">
                  {course.sourceUrl ? (
                    <a href={course.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline dark:text-blue-400">
                      {course.name}
                    </a>
                  ) : (
                    course.name
                  )}
                </td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{course.universityName}</td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">
                  <abbr title={DEGREE_LABELS[course.degreeType] ?? course.degreeType} className="cursor-help">
                    {course.degreeType}
                  </abbr>
                </td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{course.atarGuaranteed ?? "–"}</td>
                <td className="hidden sm:table-cell py-2 pr-4 text-gray-600 dark:text-gray-400">
                  {course.durationYears ? `${course.durationYears}y` : "–"}
                </td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{course.campusName ?? "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination page={page} total={total} sort={sort} dir={dir} filters={filters} />
    </div>
  );
}
