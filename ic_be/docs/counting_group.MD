# Counting Groups Docs


## schemas database

```sql
CREATE TABLE IF NOT EXISTS counting_groups (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    batch_id BIGINT NOT NULL,
    user_id_1 BIGINT NOT NULL,
    fullname_1 VARCHAR(128),
    user_id_2 BIGINT NOT NULL,
    fullname_2 VARCHAR(128),
    racks TEXT[],
    process SMALLINT NOT NULL DEFAULT 0
);
```

### descriptions

- `code` - counting group code
- `batch_id` - batch id
- `user_id_1` - first user id (Linfox)
- `fullname_1` - first user fullname (Linfox)
- `user_id_2` - second user id (Unilever)
- `fullname_2` - second user fullname (Unilever)
- `racks` - racks list
- `process` - process status
