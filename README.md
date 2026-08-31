# Nutrition FastAPI backend

Backend дневника питания для аккаунта и членов семьи. Каталог содержит пищевую
ценность продуктов на 100 г, а дневник — приёмы пищи, порции, цели, замеры и
статистику.

## Локальный запуск с SQLite

Рекомендуется Python 3.12, минимальная поддерживаемая версия — 3.9.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
alembic upgrade head
uvicorn app.main:app --reload
```

Без `DATABASE_URL` приложение использует `sqlite:///./backend.db`.

- API: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>
- Health check: <http://127.0.0.1:8000/health>

## Запуск в Docker с MariaDB

```bash
cp .env.example .env
# Перед публикацией замените пароли в .env
docker-compose up --build
```

Compose поднимает API на порту `8000`, MariaDB хранит данные в именованном томе
`mariadb_data`. Перед стартом API автоматически выполняется `alembic upgrade
head`. Остановить сервисы можно через `docker-compose down`; команда не удаляет
том с данными. `docker-compose down -v` удалит и данные, поэтому её следует
использовать только намеренно.

Если Compose установлен как Docker CLI plugin, те же команды пишутся через
`docker compose` вместо `docker-compose`.

## Подключение внешней MariaDB

При локальном запуске приложение автоматически читает `.env` из корня проекта.
Файл исключён из Git. Приложение выбирает БД через переменную `DATABASE_URL`:

```bash
export DATABASE_URL='mysql+pymysql://user:url-encoded-password@host:3306/nutrition?charset=utf8mb4'
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Пароль внутри URL должен быть URL-encoded. База и пользователь MariaDB должны
быть созданы заранее с кодировкой `utf8mb4`. Для production-секретов используйте
переменные окружения или secret manager, не добавляйте `.env` в Git.

При нескольких экземплярах API миграцию лучше запускать отдельным deployment
job, а контейнеры приложения стартовать с `RUN_MIGRATIONS=false`.

## Перенос существующих данных SQLite в MariaDB

Сначала создайте пустую схему в MariaDB:

```bash
DATABASE_URL="$TARGET_DATABASE_URL" alembic upgrade head
```

Затем перенесите данные, сохранив ID и связи:

```bash
export SOURCE_DATABASE_URL='sqlite:///./backend.db'
export TARGET_DATABASE_URL='mysql+pymysql://user:url-encoded-password@host:3306/nutrition?charset=utf8mb4'
python scripts/copy_database.py
```

Скрипт ничего не удаляет и откажется работать, если целевые таблицы уже содержат
данные. После переноса сначала сравните API и количество записей, затем
переключайте production-приложение на новый `DATABASE_URL`. Перед переносом
сделайте отдельную резервную копию `backend.db`.

## Миграции схемы

Все изменения структуры БД выполняются через Alembic:

```bash
alembic upgrade head
alembic current
```

После изменения SQLAlchemy-моделей создайте и обязательно проверьте миграцию:

```bash
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

## Основные API

- `/products`
- `/accounts`
- `/accounts/{account_id}/users`
- `/accounts/{account_id}/users/{user_id}/goals`
- `/accounts/{account_id}/users/{user_id}/goals/timeline`
- `/accounts/{account_id}/users/{user_id}/measurements`
- `/accounts/{account_id}/meals`
- `/accounts/{account_id}/meals/{meal_id}/entries`
- `/accounts/{account_id}/meals/{meal_id}/entries/batch`
- `/accounts/{account_id}/meal-days/{date}`
- `/accounts/{account_id}/meal-days/{date}/totals`
- `/accounts/{account_id}/meal-days/{target_date}/copy`
- `/accounts/{account_id}/users/{user_id}/statistics/nutrition/average`
- `/accounts/{account_id}/users/{user_id}/statistics/nutrition/timeline`

При копировании дня `source_date` обязателен. Заполненный целевой день защищён от
перезаписи; для явной замены передайте `replace_existing: true`.

## Импорт и тесты

```bash
python -m scripts.seed_products
python -m scripts.import_meals_csv "/path/to/diary.csv"
pytest
```

Импорты повторно используют существующие данные и не создают дубликаты.
`pyproject.toml` задаёт допустимые диапазоны зависимостей, а
`requirements.lock` фиксирует проверенные точные версии.

## Подготовка к Git

Локальные базы, `.env`, виртуальное окружение, IntelliJ `.idea`, логи и сборочные
файлы исключены через `.gitignore`. Файл `.env.example` содержит только пример и
должен оставаться в репозитории. Перед первым push проверьте список файлов:

```bash
git init --initial-branch=main
git status
git add .
git status
```
