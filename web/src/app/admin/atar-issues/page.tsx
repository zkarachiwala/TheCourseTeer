export const dynamic = "force-dynamic";

import { db } from "../../../../db";
import { atarIssues, universities, scrapeRuns } from "../../../../db/schema";
import { eq, asc, desc, inArray } from "drizzle-orm";
import Link from "next/link";

async function getLatestRunIds(): Promise<string[]> {
  const runs = await db
    .selectDistinctOn([scrapeRuns.universityId], { id: scrapeRuns.id })
    .from(scrapeRuns)
    .where(eq(scrapeRuns.status, "complete"))
    .orderBy(scrapeRuns.universityId, desc(scrapeRuns.runNumber));
  return runs.map(r => r.id);
}

async function getIssues(uniFilter: string, typeFilter: string) {
  const latestRunIds = await getLatestRunIds();
  if (latestRunIds.length === 0) return [];

  const rows = await db
    .select({
      id: atarIssues.id,
      courseName: atarIssues.courseName,
      courseUrl: atarIssues.courseUrl,
      issueType: atarIssues.issueType,
      description: atarIssues.description,
      createdAt: atarIssues.createdAt,
      universityName: universities.name,
      runNumber: scrapeRuns.runNumber,
    })
    .from(atarIssues)
    .innerJoin(universities, eq(atarIssues.universityId, universities.id))
    .innerJoin(scrapeRuns, eq(atarIssues.runId, scrapeRuns.id))
    .where(inArray(atarIssues.runId, latestRunIds))
    .orderBy(asc(atarIssues.issueType), asc(universities.name), asc(atarIssues.courseName));

  return rows.filter(r =>
    (!uniFilter || r.universityName === uniFilter) &&
    (!typeFilter || r.issueType === typeFilter)
  );
}

async function getFilterOptions() {
  const latestRunIds = await getLatestRunIds();
  if (latestRunIds.length === 0) return { unis: [], types: [] };

  const rows = await db
    .select({ universityName: universities.name, issueType: atarIssues.issueType })
    .from(atarIssues)
    .innerJoin(universities, eq(atarIssues.universityId, universities.id))
    .where(inArray(atarIssues.runId, latestRunIds));

  const unis = [...new Set(rows.map(r => r.universityName))].sort();
  const types = [...new Set(rows.map(r => r.issueType))].sort();
  return { unis, types };
}

const inputCls = "rounded border border-gray-200 bg-white px-2 py-1 text-xs dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100";

export default async function AtarIssuesPage({
  searchParams,
}: {
  searchParams: Promise<{ uni?: string; type?: string }>;
}) {
  const { uni, type } = await searchParams;
  const uniFilter = uni ?? "";
  const typeFilter = type ?? "";

  const [issues, filterOptions] = await Promise.all([
    getIssues(uniFilter, typeFilter),
    getFilterOptions(),
  ]);

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold">ATAR Issues</h1>
      <p className="mb-6 text-sm text-gray-500">Latest scrape run per university. {issues.length} issues shown.</p>

      <form method="get" className="mb-4 flex flex-wrap gap-3">
        <select defaultValue={uniFilter} name="uni" className={inputCls}>
          <option value="">All universities</option>
          {filterOptions.unis.map(u => <option key={u} value={u}>{u}</option>)}
        </select>
        <select defaultValue={typeFilter} name="type" className={inputCls}>
          <option value="">All issue types</option>
          {filterOptions.types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <button type="submit" className="rounded bg-gray-900 px-3 py-1 text-xs text-white hover:bg-gray-700 dark:bg-gray-100 dark:text-gray-900">
          Filter
        </button>
      </form>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="pb-2 pr-4 text-left font-medium">University</th>
              <th className="pb-2 pr-4 text-left font-medium">Course</th>
              <th className="pb-2 pr-4 text-left font-medium">Issue type</th>
              <th className="pb-2 pr-4 text-left font-medium">Description</th>
              <th className="pb-2 pr-4 text-left font-medium">Run</th>
              <th className="pb-2 text-left font-medium">Logged</th>
            </tr>
          </thead>
          <tbody>
            {issues.map(issue => (
              <tr key={issue.id} className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{issue.universityName}</td>
                <td className="py-2 pr-4">
                  <a href={issue.courseUrl} target="_blank" rel="noopener noreferrer"
                    className="text-blue-600 hover:underline dark:text-blue-400">
                    {issue.courseName}
                  </a>
                </td>
                <td className="py-2 pr-4">
                  <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-mono dark:bg-gray-800">
                    {issue.issueType}
                  </span>
                </td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{issue.description}</td>
                <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">#{issue.runNumber}</td>
                <td className="py-2 text-gray-600 dark:text-gray-400 whitespace-nowrap">
                  {issue.createdAt ? new Date(issue.createdAt).toLocaleString("en-AU") : "–"}
                </td>
              </tr>
            ))}
            {issues.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-400">No issues found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
