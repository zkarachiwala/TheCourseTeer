-- migrate:up
INSERT INTO universities (name, slug, homepage_url, scraper_status) VALUES
    ('La Trobe University',                  'latrobe',    'https://www.latrobe.edu.au',    'pending'),
    ('Deakin University',                    'deakin',     'https://www.deakin.edu.au',     'pending'),
    ('Federation University',                'federation', 'https://federation.edu.au',     'pending'),
    ('Swinburne University of Technology',   'swinburne',  'https://www.swinburne.edu.au',  'pending'),
    ('Victoria University',                  'vu',         'https://www.vu.edu.au',         'pending');

-- migrate:down
DELETE FROM universities
WHERE slug IN ('latrobe', 'deakin', 'federation', 'swinburne', 'vu');
