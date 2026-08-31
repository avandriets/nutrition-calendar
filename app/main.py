from fastapi import FastAPI

from app.accounts.router import router as accounts_router
from app.meals.router import router as meals_router
from app.nutrition_stats.router import router as nutrition_stats_router
from app.products.router import router as products_router
from app.users.router import router as users_router

app = FastAPI(
    title="TEST Backend",
    version="0.1.0",
)

app.include_router(products_router)
app.include_router(accounts_router)
app.include_router(users_router)
app.include_router(meals_router)
app.include_router(nutrition_stats_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "FastAPI backend is running"}


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
