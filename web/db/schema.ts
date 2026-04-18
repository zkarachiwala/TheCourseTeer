import {
  pgTable, uuid, text, integer, numeric, boolean, timestamp, jsonb, primaryKey,
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
