-- migrate:up
INSERT INTO campuses (university_id, name, slug, address, latitude, longitude)
SELECT u.id, c.name, c.slug, c.address, c.latitude, c.longitude
FROM universities u
JOIN (VALUES
    ('rmit',    'City Campus',   'rmit-city',          '124 La Trobe St, Melbourne VIC 3000',          -37.8080,  144.9628),
    ('monash',  'Clayton',       'monash-clayton',     'Wellington Rd, Clayton VIC 3800',              -37.9111,  145.1335),
    ('uq',      'St Lucia',      'uq-st-lucia',        'University Dr, St Lucia QLD 4067',             -27.4975,  153.0137),
    ('usyd',    'Camperdown',    'usyd-camperdown',    'Camperdown NSW 2006',                          -33.8882,  151.1876),
    ('unimelb', 'Parkville',     'unimelb-parkville',  'Grattan St, Parkville VIC 3010',              -37.7963,  144.9614)
) AS c(uni_slug, name, slug, address, latitude, longitude)
ON u.slug = c.uni_slug;

-- migrate:down
DELETE FROM campuses
WHERE slug IN ('rmit-city', 'monash-clayton', 'uq-st-lucia', 'usyd-camperdown', 'unimelb-parkville');
