import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

if (!process.env.DATABASE_URL) {
  if (process.env.NODE_ENV === 'production') {
    console.error("RUNTIME ERROR: DATABASE_URL is not set in the environment.");
  } else {
    throw new Error("DATABASE_URL is not set");
  }
}

const connectionString = process.env.DATABASE_URL || "";
if (connectionString === "" && process.env.NODE_ENV === 'production') {
  console.error("The database connection string is empty. Please check your Azure Static Web App configuration.");
}

// Supabase uses a transaction pooler on port 6543 — postgres.js works without prepare statements.
const client = postgres(connectionString, { prepare: false });

export const db = drizzle(client, { schema });
