-- migrate:up
INSERT INTO universities (name, slug, homepage_url, scraper_status) VALUES
    ('Australian Catholic University', 'acu', 'https://www.acu.edu.au', 'pending');

INSERT INTO campuses (university_id, name, slug, address, latitude, longitude)
SELECT u.id, c.name, c.slug, c.address, c.latitude, c.longitude
FROM universities u
JOIN (VALUES
    ('acu', 'Melbourne (St Patrick''s)', 'acu-melbourne', '115 Victoria Parade, Fitzroy VIC 3065', -37.8085, 144.9795),
    ('acu', 'Ballarat (Aquinas)',      'acu-ballarat',  '1200 Mair St, Ballarat Central VIC 3350', -37.5622, 143.8390)
) AS c(uni_slug, name, slug, address, latitude, longitude)
ON u.slug = c.uni_slug;

INSERT INTO campuses (university_id, name, slug, is_online)
SELECT u.id, 'Online', 'acu-online', true
FROM universities u
WHERE u.slug = 'acu';

-- migrate:down
DELETE FROM campuses WHERE university_id = (SELECT id FROM universities WHERE slug = 'acu');
DELETE FROM universities WHERE slug = 'acu';
