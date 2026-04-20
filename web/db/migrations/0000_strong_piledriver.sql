CREATE TABLE IF NOT EXISTS "atar_issues" (
	"id" uuid PRIMARY KEY NOT NULL,
	"university_id" uuid NOT NULL,
	"run_id" uuid NOT NULL,
	"course_name" text NOT NULL,
	"course_url" text NOT NULL,
	"issue_type" text NOT NULL,
	"description" text NOT NULL,
	"created_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "campuses" (
	"id" uuid PRIMARY KEY NOT NULL,
	"university_id" uuid NOT NULL,
	"name" text NOT NULL,
	"slug" text NOT NULL,
	"address" text,
	"latitude" numeric,
	"longitude" numeric,
	"is_online" boolean DEFAULT false
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "course_campuses" (
	"course_id" uuid NOT NULL,
	"campus_id" uuid NOT NULL,
	"atar_guaranteed" integer,
	"atar_lowest_selection_rank" integer,
	"extraction_notes" text,
	CONSTRAINT "course_campuses_course_id_campus_id_pk" PRIMARY KEY("course_id","campus_id")
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "courses" (
	"id" uuid PRIMARY KEY NOT NULL,
	"university_id" uuid NOT NULL,
	"name" text NOT NULL,
	"faculty" text,
	"degree_type" text NOT NULL,
	"duration_years" numeric,
	"source_url" text,
	"price_annual_csp_aud" integer,
	"price_annual_dfee_aud" integer,
	"csp_available" boolean,
	"prerequisites" jsonb,
	"updated_at" timestamp with time zone,
	"created_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "scrape_runs" (
	"id" uuid PRIMARY KEY NOT NULL,
	"university_id" uuid NOT NULL,
	"run_number" integer NOT NULL,
	"status" text DEFAULT 'in_progress' NOT NULL,
	"forced" boolean DEFAULT false,
	"discovery_complete" boolean DEFAULT false,
	"completed_at" timestamp with time zone,
	"created_at" timestamp with time zone
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "scraper_configs" (
	"id" uuid PRIMARY KEY NOT NULL,
	"university_id" uuid NOT NULL,
	"field_name" text NOT NULL,
	"selector" text NOT NULL,
	"url_path" text,
	"last_verified_at" timestamp with time zone,
	"ai_generated" boolean DEFAULT false,
	"mode" text
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "universities" (
	"id" uuid PRIMARY KEY NOT NULL,
	"name" text NOT NULL,
	"slug" text NOT NULL,
	"homepage_url" text NOT NULL,
	"scraper_status" text,
	"robots_txt_rules" jsonb,
	"last_scraped_at" timestamp with time zone
);
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "atar_issues" ADD CONSTRAINT "atar_issues_university_id_universities_id_fk" FOREIGN KEY ("university_id") REFERENCES "public"."universities"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "atar_issues" ADD CONSTRAINT "atar_issues_run_id_scrape_runs_id_fk" FOREIGN KEY ("run_id") REFERENCES "public"."scrape_runs"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "campuses" ADD CONSTRAINT "campuses_university_id_universities_id_fk" FOREIGN KEY ("university_id") REFERENCES "public"."universities"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "course_campuses" ADD CONSTRAINT "course_campuses_course_id_courses_id_fk" FOREIGN KEY ("course_id") REFERENCES "public"."courses"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "course_campuses" ADD CONSTRAINT "course_campuses_campus_id_campuses_id_fk" FOREIGN KEY ("campus_id") REFERENCES "public"."campuses"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "courses" ADD CONSTRAINT "courses_university_id_universities_id_fk" FOREIGN KEY ("university_id") REFERENCES "public"."universities"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "scrape_runs" ADD CONSTRAINT "scrape_runs_university_id_universities_id_fk" FOREIGN KEY ("university_id") REFERENCES "public"."universities"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "scraper_configs" ADD CONSTRAINT "scraper_configs_university_id_universities_id_fk" FOREIGN KEY ("university_id") REFERENCES "public"."universities"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "atar_issues_university_id" ON "atar_issues" USING btree ("university_id");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "atar_issues_run_id" ON "atar_issues" USING btree ("run_id");--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "scrape_runs_university_id" ON "scrape_runs" USING btree ("university_id");