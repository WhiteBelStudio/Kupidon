from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter,Depends,File,HTTPException,Request,UploadFile
from pydantic import BaseModel,Field,field_validator
from backend.auth import current_user

router=APIRouter()

class ProfileInput(BaseModel):
    age:int=Field(ge=14,le=25)
    city:str=Field(min_length=1,max_length=100)
    gender:str
    target_gender:str
    bio:str=Field(default="",max_length=1000)
    interests:str=Field(default="",max_length=500)
    @field_validator("gender")
    @classmethod
    def gender_ok(cls,v):
        if v not in {"male","female"}: raise ValueError("Invalid gender")
        return v
    @field_validator("target_gender")
    @classmethod
    def target_ok(cls,v):
        if v not in {"male","female","any"}: raise ValueError("Invalid target gender")
        return v

@router.get("/profile")
async def get_profile(request:Request,user:dict=Depends(current_user)):
    return {"profile":await request.app.state.db.get_profile(user["id"])}

@router.post("/profile")
async def save_profile(payload:ProfileInput,request:Request,user:dict=Depends(current_user)):
    return {"profile":await request.app.state.db.save_profile(user["id"],payload.model_dump())}

@router.post("/profile/photo")
async def upload_photo(request:Request,file:UploadFile=File(...),user:dict=Depends(current_user)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400,"Only image files are allowed")
    content=await file.read()
    if len(content)>5*1024*1024: raise HTTPException(413,"Image is too large")
    ext=Path(file.filename or "").suffix.lower()
    if ext not in {".jpg",".jpeg",".png",".webp"}: ext=".jpg"
    name=f"{user['id']}_{uuid4().hex}{ext}"
    Path(request.app.state.settings.upload_dir,name).write_bytes(content)
    await request.app.state.db.set_photo(user["id"],name)
    return {"photo_path":name}
