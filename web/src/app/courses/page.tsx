export const dynamic = "force-dynamic";

import { db } from "../../../db";
import { courses, universities, courseCampuses, campuses } from "../../../db/schema";
import { eq, asc, desc, sql } from "drizzle-orm";
import Link from "next/link";

const PAGE_SIZE = 25;

type SortCol = "name" | "university" | "type" | "duration";
type SortDir = "asc" | "desc";

const SORT_COLUMNS = {
  name: courses.name,
  university: universities.name,
  type: courses.degreeType,
  duration: courses.durationYears,
} as const;

type CampusSummary = { name: string; atar: number | null };

type CourseRow = {
  id: string;
  name: string;
  sourceUrl: string | null;
  degreeType: string;
  durationYears: string | null;
  universityName: string;
  campuses: CampusSummary[];
};

async function getCourses(sort: SortCol, dir: SortDir, page: number) {
  const col = SORT_COLUMNS[sort];
  const order = dir === "asc" ? asc(col) : desc(col);
  const offset = (page - 1) * PAGE_SIZE;

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
      .orderBy(order)
      .limit(PAGE_SIZE)
      .offset(offset),
    db.select({ total: sql<number>`count(distinct ${courses.id})` }).from(courses),
  ]);

  const map = new Map<string, CourseRow>();
  for (const row of rows) {
    if (!map.has(row.id)) {
      map.set(row.id, {
        id: row.id,
        name: row.name,
        sourceUrl: row.sourceUrl,
        degreeType: row.degreeType,
        durationYears: row.durationYears,
        universityName: row.universityName,
        campuses: [],
      });
    }
    if (row.campusName) {
      map.get(row.id)!.campuses.push({ name: row.campusName, atar: row.atarGuaranteed });
    }
  }

  return { rows: Array.from(map.values()), total: Number(total) };
}

function colUrl(col: SortCol, current: SortCol, dir: SortDir) {
  const nextDir = col === current && dir === "asc" ? "desc" : "asc";
  return `/courses?sort=${col}&dir=${nextDir}&page=1`;
}

function SortHeader({ col, label, current, dir }: { col: SortCol; label: string; current: SortCol; dir: SortDir }) {
  const active = col === current;
  const indicator = active ? (dir === "asc" ? " ↑" : " ↓") : "";
  return (
    <th className="pb-2 pr-4 text-left font-medium">
      <Link href={colUrl(col, current, dir)} className={active ? "underline underline-offset-2" : "hover:underline hover:underline-offset-2"}>
        {label}{indicator}
      </Link>
    </th>
  );
}

function Pagination({ page, total, sort, dir }: { page: number; total: number; sort: SortCol; dir: SortDir }) {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  if (totalPages <= 1) return null;
  const base = `/courses?sort=${sort}&dir=${dir}`;
  return (
    <div className="mt-6 flex items-center justify-between text-sm">
      <span className="text-gray-500 dark:text-gray-400">Page {page} of {totalPages}</span>
      <div className="flex gap-2">
        {page > 1 && (
          <Link href={`${base}&page=${page - 1}`} className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800">
            Previous
          </Link>
        )}
        {page < totalPages && (
          <Link href={`${base}&page=${page + 1}`} className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800">
            Next
          </Link>
        )}
      </div>
    </div>
  );
}

const VALID_SORTS: SortCol[] = ["name", "university", "type", "duration"];

export default async function CoursesPage({
  searchParams,
}: {
  searchParams: { sort?: string; dir?: string; page?: string };
}) {
  const sort = (VALID_SORTS.includes(searchParams.sort as SortCol) ? searchParams.sort : "name") as SortCol;
  const dir: SortDir = searchParams.dir === "desc" ? "desc" : "asc";
  const page = Math.max(1, parseInt(searchParams.page ?? "1", 10) || 1);

  const { rows: courseList, total } = await getCourses(sort, dir, page);
  const start = (page - 1) * PAGE_SIZE + 1;
  const end = Math.min(page * PAGE_SIZE, total);

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Courses</h1>
      <p className="mb-4 text-sm text-gray-500">
        {total > 0 ? `Showing ${start}–${end} of ${total} courses` : "No courses found"}
      </p>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <SortHeader col="name" label="Course" current={sort} dir={dir} />
              <SortHeader col="university" label="University" current={sort} dir={dir} />
              <SortHeader col="type" label="Type" current={sort} dir={dir} />
              <SortHeader col="duration" label="Duration" current={sort} dir={dir} />
              <th className="pb-2 text-left font-medium">Campuses / ATAR</th>
            </tr>
          </thead>
          <tbody>
            {courseList.map((course) => (
              <tr key={course.id} className="border-b border-gray-100 dark:border-gray-800">
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
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{course.degreeType}</td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">
                  {course.durationYears ? `${course.durationYears}y` : "-"}
                </td>
                <td className="py-2 text-gray-600 dark:text-gray-400">
                  {course.campuses.map((c) => (c.atar ? `${c.name} (${c.atar})` : c.name)).join(", ") || "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination page={page} total={total} sort={sort} dir={dir} />
    </div>
  );
}
