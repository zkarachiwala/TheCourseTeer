-- migrate:up
DELETE FROM campuses WHERE id = '78dae243-37b7-458c-91a2-c5926b7c69b5'; -- Footscray City (wrong name — duplicate of Footscray Park)

INSERT INTO campuses (id, university_id, name, slug, is_online)
VALUES (
    gen_random_uuid(),
    '76f950f6-4ff8-4a54-b3ad-f194221ece1c',
    'Footscray Nicholson',
    'vu-footscray-nicholson',
    false
);

-- migrate:down
-- Cannot restore deleted campus or generated UUID deterministically
