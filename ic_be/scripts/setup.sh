#!/bin/bash
set -e

DB_CONTAINER=postgres_db
DB_USER=${POSTGRES_USER:-postgres}
DB_NAME=${POSTGRES_DB:-postgres}
DB_HOST=${POSTGRES_SERVER:-postgres_db}
DB_PASSWORD=${POSTGRES_PASSWORD:-postgres}

echo "🚀 Starting migration..."


# Đợi DB sẵn sàng (thử kết nối)
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "⏳ Waiting for database to be ready..."
  echo "🔧 Trying to connect to $DB_HOST:$POSTGRES_PORT as $DB_USER"
  sleep 2
done

# Chạy từng file .sql trong thư mục upgrade
for f in app/migrations/upgrade/*.sql; do
  echo "👉 Running migration: $f"
  PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "$f" || true
done

echo "✅ All migrations applied successfully!"

# Thêm tenant
PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<EOF
INSERT INTO tenants (name, description)
VALUES ('Linfox', 'LINFOX VIET NAM')
ON CONFLICT DO NOTHING;
EOF

echo "✅ Tenant inserted successfully!"

echo "🚀 Creating admin user..."
make create-admin-default
make import-temp-data
echo "✅ Setup successfully!"
