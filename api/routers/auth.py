from fastapi import APIRouter,Depends
from backend.auth import current_user
router=APIRouter()
@router.get("/me")
async def me(user:dict=Depends(current_user)):
    return {"user":user}
