export const dynamic = "force-dynamic";

import { db } from "../../../db";
import { courses, universities, courseCampuses, campuses } from "../../../db/schema";
import { eq } from "drizzle-orm";

type CampusSummary = { name: string; atar: number | null };

type CourseRow = {
  id: string;
  name: string;
  sourceUrl: string | null;
  degreeType: string | null;
  durationYears: string | null;
  universityName: string;
  campuses: CampusSummary[];
};

async function getCourses(): Promise<CourseRow[]> {
  const rows = await db
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
    .orderBy(universities.name, courses.name);

  // Collapse multiple campus rows per course
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
  return Array.from(map.values());
}

export default async function CoursesPage() {
  const courseList = await getCourses();

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Courses</h1>
      <p className="mb-4 text-sm text-gray-500">{courseList.length} courses</p>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left dark:border-gray-700">
              <th className="pb-2 pr-4 font-medium">Course</th>
              <th className="pb-2 pr-4 font-medium">University</th>
              <th className="pb-2 pr-4 font-medium">Type</th>
              <th className="pb-2 pr-4 font-medium">Duration</th>
              <th className="pb-2 font-medium">Campuses / ATAR</th>
            </tr>
          </thead>
          <tbody>
            {courseList.map((course) => (
              <tr key={course.id} className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-2 pr-4">
                  {course.sourceUrl ? (
                    <a
                      href={course.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {course.name}
                    </a>
                  ) : (
                    course.name
                  )}
                </td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{course.universityName}</td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{course.degreeType ?? "-"}</td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">
                  {course.durationYears ? `${course.durationYears}y` : "-"}
                </td>
                <td className="py-2 text-gray-600 dark:text-gray-400">
                  {course.campuses
                    .map((c) => (c.atar ? `${c.name} (${c.atar})` : c.name))
                    .join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
