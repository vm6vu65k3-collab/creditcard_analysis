-- Running upgrade 1aea27fe0d54 -> bdc8a023725f

ALTER TABLE chart_requests ADD COLUMN test VARCHAR(30);

UPDATE alembic_version SET version_num='bdc8a023725f' WHERE alembic_version.version_num = '1aea27fe0d54';

