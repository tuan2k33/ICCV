# 🚀 FastAPI Backend Starter

This is a backend project built with **FastAPI**, structured with a clear modular architecture to ensure scalability and maintainability. It includes JWT authentication, user management, role-based authorization, and environment-based configuration support.

## 📁 Project Structure

```bash
.
├── app
│   ├── constant/            # Application-wide constants and enums
│   ├── core/                # App configuration (env, settings)
│   ├── infra/               # Infrastructure layer: database connection
│   ├── migrations/          # SQL migration scripts
│   ├── modules/             # Main modules (auth, task,...)
│   ├── utils/               # Utility functions (hashing, response formatting,...)
│   └── main.py              # Entry point of the application
├── poetry.lock              # Dependency lock file
├── pyproject.toml           # Poetry configuration file
├── README.md                # This document
└── test_main.http           # HTTP test file for quick API testing
```

## ⚙️ Setup & Run

### 1. Clone the project

```bash
git clone git@github.com:RS-DRI-O/AI_IC_BE.git
cd AI_IC_BE
```

### 2. Install Poetry
for linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install poetry
```
for Windows
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install poetry
```
> Make sure you're using Python 3.10+

### 3. Install dependencies

```bash
poetry install
```

### 4. Run the FastAPI server

```bash
poetry run uvicorn app.main:app --reload
```

> Server runs at `http://localhost:8000`


### 5. Using Docker (Optional)
on Windown
```bash
set PATH_DATA=./data
docker compose up -d
bash scripts/setup.sh
```

on Linux
```bash
PATH_DATA=./data docker compose up -d --build
chmod +x scripts/setup.sh
scripts/setup.sh
```



## 🔐 Authentication & Authorization

* Uses JWT for stateless authentication
* Role-based access control via middleware
* Roles are defined in `app/constant/enums.py`

## 🧪 Quick Testing

Use the `test_main.http` file to quickly test APIs.

> You can use the **REST Client** extension in VSCode to run this file.

## 🛠 Core Modules

| Module       | Description                               |
| ------------ | ----------------------------------------- |
| `auth`       | Handles registration, login, and JWT auth |
| `task`       | Placeholder for future business logic     |
| `infra`      | Database connection and infra utilities   |
| `utils`      | Shared utilities                          |
| `migrations` | SQL-based database migration scripts      |

## 📌 Notes

* This project uses **raw SQL scripts** for schema migrations instead of tools like Alembic.
* `__pycache__/` folders are ignored for production deployments.
* Environment configurations are loaded from variables and defined in `app/core/setting.py`.

## 📄 License

MIT License
