import {
  pgTable, uuid, text, integer, numeric, boolean, timestamp, jsonb, primaryKey, index,
} from "drizzle-orm/pg-core";

export const universities = pgTable("universities", {
  id: uuid("id").primaryKey(),
  name: text("name").notNull(),
  slug: text("slug").notNull(),
  homepageUrl: text("homepage_url").notNull(),
  scraperStatus: text("scraper_status"),
  robotsTxtRules: jsonb("robots_txt_rules"),
  lastScrapedAt: timestamp("last_scraped_at", { withTimezone: true }),
});

export const campuses = pgTable("campuses", {
  id: uuid("id").primaryKey(),
  universityId: uuid("university_id").notNull().references(() => universities.id),
  name: text("name").notNull(),
  slug: text("slug").notNull(),
  address: text("address"),
  latitude: numeric("latitude"),
  longitude: numeric("longitude"),
  isOnline: boolean("is_online").default(false),
});

export const courses = pgTable("courses", {
  id: uuid("id").primaryKey(),
  universityId: uuid("university_id").notNull().references(() => universities.id),
  name: text("name").notNull(),
  faculty: text("faculty"),
  degreeType: text("degree_type").notNull(),
  durationYears: numeric("duration_years"),
  sourceUrl: text("source_url"),
  priceAnnualCspAud: integer("price_annual_csp_aud"),
  priceAnnualDfeeAud: integer("price_annual_dfee_aud"),
  cspAvailable: boolean("csp_available"),
  prerequisites: jsonb("prerequisites"),
  updatedAt: timestamp("updated_at", { withTimezone: true }),
  createdAt: timestamp("created_at", { withTimezone: true }),
});

export const courseCampuses = pgTable("course_campuses", {
  courseId: uuid("course_id").notNull().references(() => courses.id),
  campusId: uuid("campus_id").notNull().references(() => campuses.id),
  atarGuaranteed: integer("atar_guaranteed"),
  atarLowestSelectionRank: integer("atar_lowest_selection_rank"),
  extractionNotes: text("extraction_notes"),
}, (t) => [primaryKey({ columns: [t.courseId, t.campusId] })]);

export const scrapeRuns = pgTable("scrape_runs", {
  id: uuid("id").primaryKey(),
  universityId: uuid("university_id").notNull().references(() => universities.id),
  runNumber: integer("run_number").notNull(),
  status: text("status").notNull().default("in_progress"),
  forced: boolean("forced").default(false),
  discoveryComplete: boolean("discovery_complete").default(false),
  completedAt: timestamp("completed_at", { withTimezone: true }),
  createdAt: timestamp("created_at", { withTimezone: true }),
}, (t) => [index("scrape_runs_university_id").on(t.universityId)]);

export const scraperConfigs = pgTable("scraper_configs", {
  id: uuid("id").primaryKey(),
  universityId: uuid("university_id").notNull().references(() => universities.id),
  fieldName: text("field_name").notNull(),
  selector: text("selector").notNull(),
  lastVerifiedAt: timestamp("last_verified_at", { withTimezone: true }),
  aiGenerated: boolean("ai_generated").default(false),
  mode: text("mode"),
});

export const atarIssues = pgTable("atar_issues", {
  id: uuid("id").primaryKey(),
  universityId: uuid("university_id").notNull().references(() => universities.id),
  runId: uuid("run_id").notNull().references(() => scrapeRuns.id),
  courseName: text("course_name").notNull(),
  courseUrl: text("course_url").notNull(),
  issueType: text("issue_type").notNull(),
  description: text("description").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }),
}, (t) => [
  index("atar_issues_university_id").on(t.universityId),
  index("atar_issues_run_id").on(t.runId),
]);
