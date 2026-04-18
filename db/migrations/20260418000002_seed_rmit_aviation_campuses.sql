-- migrate:up

INSERT INTO campuses (university_id, name, slug, address, latitude, longitude)
SELECT u.id, c.name, c.slug, c.address, c.latitude, c.longitude
FROM universities u
JOIN (VALUES
    ('rmit', 'Point Cook', 'rmit-point-cook', 'RAAF Williams Base, Point Cook VIC 3029', -37.9320, 144.7543),
    ('rmit', 'Bendigo',    'rmit-bendigo',    '35 Victa Rd, East Bendigo VIC 3550',      -36.7172, 144.3685)
) AS c(uni_slug, name, slug, address, latitude, longitude)
ON u.slug = c.uni_slug;

-- migrate:down

DELETE FROM campuses WHERE slug IN ('rmit-point-cook', 'rmit-bendigo');
