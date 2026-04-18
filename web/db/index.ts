import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is not set");

// Supabase uses a transaction pooler on port 6543 — postgres.js works without prepare statements.
const client = postgres(process.env.DATABASE_URL, { prepare: false });

export const db = drizzle(client, { schema });
