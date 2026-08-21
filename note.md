
## Đẩy 1 file json output AI
source ~/.bash_aliases
put_ai <path_to_dict_total.json> [tenant_id_macdinh1]



## Reset DB dãy trên TablePlus
docker run --rm -v /Users/thaokhuu/Desktop:/backup -e PGPASSWORD=postgres postgres:latest sh -c 'psql -h 192.168.1.200 -p 5435 -d postgres -U postgres -f /backup/0001_demov2.sql'


## Xóa user 
docker exec inventory_count_postgres_db psql -U postgres -d postgres -c "DELETE FROM users WHERE id != 1 RETURNING id, username;"

## Lưu Snapshot
docker run --rm -v /ssd1/inventory_count/snapshot:/dump -e PGPASSWORD=postgres postgres pg_dump -h 192.168.1.200 -p 5435 -U postgres -d postgres > /ssd1/inventory_count/snapshot/init-clean-db.sql


## Run Snapshot
docker run --rm -v /ssd1/inventory_count/snapshot:/backup -e PGPASSWORD=postgres postgres:latest sh -c 'psql -h 192.168.1.200 -p 5435 -d postgres -U postgres -f /backup/init-clean-db.sql'



## Update đếm 1 nửa
docker exec inventory_count_postgres_db psql -U postgres -d postgres -c "UPDATE tasks SET status = 'IN_PROGRESS', result_c = NULL, time_process_e = (SELECT jsonb_object_agg(key, COALESCE(time_process_e -> key, '{}'::jsonb)) FROM jsonb_object_keys(result_e) AS key) WHERE rack_name = 'AX-odd';"




