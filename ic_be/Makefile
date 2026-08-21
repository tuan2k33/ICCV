.PHONY: run create-admin

# Run app
run:
	python -m app.main

create-admin:
	@read -p "👤 Username: " username; \
	read -p "📧 Email: " email; \
	read -p "🔑 Password: " password; \
	python -m app.scripts.create_admin \
		--username $$username \
		--email $$email \
		--password $$password

create-admin-default:
	python -m app.scripts.create_admin \
		--username admin \
		--email admin@admin.com \
		--password Rsc@2025

import-temp-data:
	python -m app.scripts.setup_temp_data