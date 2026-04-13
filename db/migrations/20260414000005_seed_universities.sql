-- migrate:up
INSERT INTO universities (name, slug, homepage_url, scraper_status) VALUES
    ('RMIT University',           'rmit',    'https://www.rmit.edu.au',      'pending'),
    ('Monash University',         'monash',  'https://www.monash.edu',        'pending'),
    ('University of Queensland',  'uq',      'https://www.uq.edu.au',         'pending'),
    ('University of Sydney',      'usyd',    'https://www.sydney.edu.au',     'pending'),
    ('University of Melbourne',   'unimelb', 'https://www.unimelb.edu.au',    'pending');

-- migrate:down
DELETE FROM universities
WHERE slug IN ('rmit', 'monash', 'uq', 'usyd', 'unimelb');
