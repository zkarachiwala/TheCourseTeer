-- migrate:up

-- Physical campuses for Victorian universities (is_online defaults to false)
INSERT INTO campuses (university_id, name, slug, address, latitude, longitude)
SELECT u.id, c.name, c.slug, c.address, c.latitude, c.longitude
FROM universities u
JOIN (VALUES
    -- RMIT (City Campus already seeded)
    ('rmit',       'Brunswick',              'rmit-brunswick',         '25 Dawson St, Brunswick VIC 3056',               -37.7738, 144.9612),
    ('rmit',       'Bundoora',               'rmit-bundoora',          'Plenty Rd, Bundoora VIC 3083',                   -37.7074, 145.0546),
    -- Monash (Clayton already seeded)
    ('monash',     'Caulfield',              'monash-caulfield',       '900 Dandenong Rd, Caulfield East VIC 3145',      -37.8775, 145.0444),
    ('monash',     'Peninsula',              'monash-peninsula',       'McMahons Rd, Frankston VIC 3199',                -38.1479, 145.1293),
    ('monash',     'Parkville',              'monash-parkville',       '381 Royal Parade, Parkville VIC 3052',           -37.7865, 144.9592),
    -- UniMelb (Parkville already seeded)
    ('unimelb',    'Southbank',              'unimelb-southbank',      'Southbank VIC 3006',                             -37.8230, 144.9644),
    -- La Trobe
    ('latrobe',    'Bundoora',               'latrobe-bundoora',       'Plenty Rd, Bundoora VIC 3086',                   -37.7215, 145.0492),
    ('latrobe',    'Bendigo',                'latrobe-bendigo',        'Edwards Rd, Bendigo VIC 3550',                   -36.7411, 144.2981),
    ('latrobe',    'Albury-Wodonga',         'latrobe-albury-wodonga', 'Kiewa St, Albury NSW 2640',                      -36.0785, 146.9204),
    ('latrobe',    'Melbourne City',         'latrobe-melbourne-city', '360 Collins St, Melbourne VIC 3000',             -37.8179, 144.9637),
    -- Deakin
    ('deakin',     'Geelong Waurn Ponds',    'deakin-waurn-ponds',     'Pigdons Rd, Waurn Ponds VIC 3216',              -38.1985, 144.3019),
    ('deakin',     'Geelong Waterfront',     'deakin-waterfront',      '1 Gheringhap St, Geelong VIC 3220',              -38.1471, 144.3600),
    ('deakin',     'Melbourne Burwood',      'deakin-burwood',         '221 Burwood Hwy, Burwood VIC 3125',              -37.8477, 145.1150),
    ('deakin',     'Warrnambool',            'deakin-warrnambool',     'Princes Hwy, Warrnambool VIC 3280',              -38.3792, 142.4850),
    -- Federation University
    ('federation', 'Ballarat Mt Helen',      'federation-mt-helen',    'University Dr, Mount Helen VIC 3350',            -37.5509, 143.8616),
    ('federation', 'Gippsland Churchill',    'federation-churchill',   'Northways Rd, Churchill VIC 3842',               -38.3054, 146.4233),
    ('federation', 'Berwick',                'federation-berwick',     '100 Clyde Rd, Berwick VIC 3806',                 -38.0333, 145.3528),
    -- Swinburne
    ('swinburne',  'Hawthorn',               'swinburne-hawthorn',     'John St, Hawthorn VIC 3122',                     -37.8213, 145.0387),
    ('swinburne',  'Wantirna',               'swinburne-wantirna',     'Stud Rd, Wantirna South VIC 3152',               -37.8600, 145.2250),
    -- Victoria University
    ('vu',         'Footscray Park',         'vu-footscray-park',      'Ballarat Rd, Footscray VIC 3011',                -37.7973, 144.8950),
    ('vu',         'Footscray City',         'vu-footscray-city',      'Nicholson St, Footscray VIC 3011',               -37.8002, 144.9000),
    ('vu',         'Sunshine',               'vu-sunshine',            'Cnr Ballarat & Forrest Sts, Sunshine VIC 3020',  -37.7870, 144.8320),
    ('vu',         'St Albans',              'vu-st-albans',           'Gillies St, St Albans VIC 3021',                 -37.7440, 144.8026),
    ('vu',         'City Flinders',          'vu-city-flinders',       '300 Flinders St, Melbourne VIC 3000',            -37.8188, 144.9660)
) AS c(uni_slug, name, slug, address, latitude, longitude)
ON u.slug = c.uni_slug;

-- Online campus (is_online = true) for all 8 Victorian universities
INSERT INTO campuses (university_id, name, slug, is_online)
SELECT u.id, 'Online', u.slug || '-online', true
FROM universities u
WHERE u.slug IN ('rmit', 'monash', 'unimelb', 'latrobe', 'deakin', 'federation', 'swinburne', 'vu');

-- migrate:down
DELETE FROM campuses
WHERE slug IN (
    'rmit-brunswick', 'rmit-bundoora',
    'monash-caulfield', 'monash-peninsula', 'monash-parkville',
    'unimelb-southbank',
    'latrobe-bundoora', 'latrobe-bendigo', 'latrobe-albury-wodonga', 'latrobe-melbourne-city',
    'deakin-waurn-ponds', 'deakin-waterfront', 'deakin-burwood', 'deakin-warrnambool',
    'federation-mt-helen', 'federation-churchill', 'federation-berwick',
    'swinburne-hawthorn', 'swinburne-wantirna',
    'vu-footscray-park', 'vu-footscray-city', 'vu-sunshine', 'vu-st-albans', 'vu-city-flinders',
    'rmit-online', 'monash-online', 'unimelb-online', 'latrobe-online',
    'deakin-online', 'federation-online', 'swinburne-online', 'vu-online'
);
