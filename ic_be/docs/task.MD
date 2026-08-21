# Counting Groups Docs


## schemas database

```sql
CREATE TABLE tasks (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT,
    batch_id BIGINT,
    version INT DEFAULT 0,
    rack_name VARCHAR,
    user_e BIGINT,
    user_view_e BIGINT,
    user_c BIGINT,
    result_e JSONB,
    result_c JSONB,
    time_process_e JSONB,
    time_process_c JSONB,
    flags_e JSONB,
    flags_c JSONB,
    time_submit_e TIMESTAMP,
    time_submit_c TIMESTAMP,
    report_task JSONB,
    release BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'NOT_STARTED',
    start_time_working TIMESTAMP,
    progress INT DEFAULT 0,
    total_progress INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

### descriptions

- `id` - task id
- `tenant_id` - tenant id
- `batch_id` - batch id
- `version` - version of the task
- `rack_name` - rack name
- `user_e` - user id who executed the task (Unilever employee)
- `user_view_e` - user id who viewed the executed task (Linfox employee)
- `user_c` - user id who checked the task (Other employee)
- `result_e` - result of the executed task
- `result_c` - result of the checked task
- `time_process_e` - time taken to execute the task
- `time_process_c` - time taken to check the task
- `flags_e` - flags of the executed task
- `flags_c` - flags of the checked task
- `time_submit_e` - time when the task was submitted
- `time_submit_c` - time when the task was checked
- `report_task` - report of the task
- `release` - flag of the release of the task
- `status` - status of the task
- `start_time_working` - time when the task started working
- `progress` - progress of the task
- `total_progress` - total progress of the task
- `created_at` - time when the task was created
- `updated_at` - time when the task was updated