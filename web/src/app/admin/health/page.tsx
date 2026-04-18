export const dynamic = "force-dynamic";

import { db } from "../../../../db";
import { universities, courses, scrapeRuns, scraperConfigs } from "../../../../db/schema";
import { eq, sql, desc, and } from "drizzle-orm";

const STATUS_STYLES: Record<string, string> = {
  last_ok:       "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
  failing:       "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  robots_blocked:"bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300",
};

async function getHealthData() {
  const unis = await db.select().from(universities).orderBy(universities.name);

  const courseCounts = await db
    .select({ universityId: courses.universityId, count: sql<number>`count(*)` })
    .from(courses)
    .groupBy(courses.universityId);

  const latestRuns = await db
    .selectDistinctOn([scrapeRuns.universityId], {
      universityId: scrapeRuns.universityId,
      runNumber: scrapeRuns.runNumber,
      completedAt: scrapeRuns.completedAt,
    })
    .from(scrapeRuns)
    .orderBy(scrapeRuns.universityId, desc(scrapeRuns.runNumber));

  const aiSelectors = await db
    .select({ universityId: scraperConfigs.universityId, count: sql<number>`count(*)` })
    .from(scraperConfigs)
    .where(eq(scraperConfigs.aiGenerated, true))
    .groupBy(scraperConfigs.universityId);

  const courseCountMap = Object.fromEntries(courseCounts.map(r => [r.universityId, Number(r.count)]));
  const latestRunMap = Object.fromEntries(latestRuns.map(r => [r.universityId, r]));
  const aiSelectorMap = Object.fromEntries(aiSelectors.map(r => [r.universityId, Number(r.count)]));

  return unis.map(u => ({
    ...u,
    courseCount: courseCountMap[u.id] ?? 0,
    latestRun: latestRunMap[u.id] ?? null,
    aiSelectorCount: aiSelectorMap[u.id] ?? 0,
  }));
}

export default async function HealthPage() {
  const rows = await getHealthData();

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Scraper Health</h1>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="pb-2 pr-6 text-left font-medium">University</th>
              <th className="pb-2 pr-6 text-left font-medium">Status</th>
              <th className="pb-2 pr-6 text-left font-medium">Last scraped</th>
              <th className="pb-2 pr-6 text-left font-medium">Run #</th>
              <th className="pb-2 pr-6 text-left font-medium">Courses</th>
              <th className="pb-2 text-left font-medium">AI selectors</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(u => (
              <tr key={u.id} className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-2 pr-6">
                  <a href={u.homepageUrl} target="_blank" rel="noopener noreferrer"
                    className="text-blue-600 hover:underline dark:text-blue-400">
                    {u.name}
                  </a>
                </td>
                <td className="py-2 pr-6">
                  {u.scraperStatus ? (
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[u.scraperStatus] ?? "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"}`}>
                      {u.scraperStatus}
                    </span>
                  ) : (
                    <span className="text-gray-400">–</span>
                  )}
                </td>
                <td className="py-2 pr-6 text-gray-600 dark:text-gray-400">
                  {u.lastScrapedAt ? new Date(u.lastScrapedAt).toLocaleString("en-AU") : "–"}
                </td>
                <td className="py-2 pr-6 text-gray-600 dark:text-gray-400">
                  {u.latestRun ? `#${u.latestRun.runNumber}` : "–"}
                </td>
                <td className="py-2 pr-6 text-gray-600 dark:text-gray-400">
                  {u.courseCount}
                </td>
                <td className="py-2 text-gray-600 dark:text-gray-400">
                  {u.aiSelectorCount > 0 ? (
                    <span className="text-yellow-600 dark:text-yellow-400">{u.aiSelectorCount}</span>
                  ) : "0"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
