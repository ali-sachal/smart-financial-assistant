from fastapi import APIRouter

from app.api.endpoints import auth, chat, finance, healthcheck, receipts

api_router = APIRouter()
api_router.include_router(healthcheck.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(finance.router, tags=["Finance"])
api_router.include_router(receipts.router, prefix="/receipts", tags=["Receipts"])
api_router.include_router(chat.router, tags=["Assistant"])
