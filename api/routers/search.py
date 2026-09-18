from fastapi import APIRouter,Depends,Request,Query
from backend.auth import current_user
router=APIRouter()

@router.get("/search")
async def search(request:Request,limit:int=Query(default=20,ge=1,le=50),user:dict=Depends(current_user)):
    profiles=await request.app.state.db.search_profiles(user["id"],limit)
    base=request.app.state.settings.api_url.rstrip("/")
    for p in profiles:
        if p.get("photo_path"): p["photo_url"]=f"{base}/media/{p['photo_path']}"
    return {"profiles":profiles}
