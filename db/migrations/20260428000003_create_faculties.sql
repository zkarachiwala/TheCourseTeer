-- Create faculties table for DB-driven mapping
CREATE TABLE IF NOT EXISTS faculties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed with current hardcoded keywords
INSERT INTO faculties (name, keywords) VALUES
('Faculty of Engineering', '{"engineering", "electrical", "civil", "mechanical", "chemical", "aerospace", "biomedical", "mechatronics", "materials"}'),
('Faculty of Information Technology', '{"information technology", "computer science", "computing", "data science", "cybersecurity", "artificial intelligence", "software"}'),
('Faculty of Business and Economics', '{"business", "commerce", "economics", "accounting", "finance", "marketing", "management", "actuarial"}'),
('Faculty of Law', '{"laws", "legal studies", "legal"}'),
('Faculty of Medicine and Health Sciences', '{"medicine", "medical", "nursing", "pharmacy", "physiotherapy", "nutrition", "dietetics", "paramedicine", "occupational therapy", "speech pathology", "radiation therapy", "dentistry", "biomedicine", "health sciences"}'),
('Faculty of Science', '{"science", "biology", "chemistry", "physics", "mathematics", "statistics", "genetics", "microbiology", "neuroscience", "environmental science"}'),
('Faculty of Arts and Humanities', '{"arts", "humanities", "history", "philosophy", "languages", "literature", "creative writing", "criminology", "politics", "sociology", "communications", "journalism", "psychology"}'),
('Faculty of Education', '{"education", "teaching"}'),
('Faculty of Art, Design and Architecture', '{"design", "architecture", "fine art", "fashion", "interior design", "industrial design", "music", "film", "animation", "media arts"}')
ON CONFLICT (name) DO UPDATE SET keywords = EXCLUDED.keywords;
