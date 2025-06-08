from fastapi import APIRouter
from app.api.v1.endpoints import user, wallet, admin, record

router = APIRouter()

router.include_router(user.router, prefix="/user", tags=["users"])
router.include_router(wallet.router, prefix="/wallet", tags=["wallet"]) 
router.include_router(admin.router, prefix="/admin", tags=["admin"]) 
router.include_router(record.router, prefix="/record", tags=["record"]) 