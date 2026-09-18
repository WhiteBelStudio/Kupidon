from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup,WebAppInfo
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from backend.auth import current_user
router=APIRouter()

class ReactionInput(BaseModel): action:str
class ReportInput(BaseModel): reason:str=Field(min_length=3,max_length=1000)

async def notify_match(request,user_id,other_id):
    bot=request.app.state.bot; db=request.app.state.db
    keyboard=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Открыть КУПИДОН",web_app=WebAppInfo(url=request.app.state.settings.webapp_url))]])
    text="🤝 <b>Взаимный интерес к дружбе!</b>\nОткрой КУПИДОН, чтобы посмотреть совпадение."
    for uid in (user_id,other_id):
        user=await db.get_user_by_id(uid)
        if user:
            try: await bot.send_message(user["telegram_id"],text,reply_markup=keyboard)
            except Exception: pass

@router.post("/users/{target_id}/reaction")
async def reaction(target_id:int,payload:ReactionInput,request:Request,user:dict=Depends(current_user)):
    if payload.action not in {"like","skip"}: raise HTTPException(400,"Invalid action")
    target=await request.app.state.db.get_user_by_id(target_id)
    if not target or target["is_blocked"]: raise HTTPException(404,"User not found")
    matched,match_id=await request.app.state.db.react(user["id"],target_id,payload.action)
    if matched: await notify_match(request,user["id"],target_id)
    return {"matched":matched,"match_id":match_id}

@router.get("/matches")
async def matches(request:Request,user:dict=Depends(current_user)):
    return {"matches":await request.app.state.db.get_matches(user["id"])}

@router.post("/users/{target_id}/block")
async def block(target_id:int,request:Request,user:dict=Depends(current_user)):
    if target_id==user["id"]: raise HTTPException(400,"Cannot block yourself")
    await request.app.state.db.block(user["id"],target_id)
    return {"ok":True}

@router.post("/users/{target_id}/report")
async def report(target_id:int,payload:ReportInput,request:Request,user:dict=Depends(current_user)):
    if target_id==user["id"]: raise HTTPException(400,"Cannot report yourself")
    await request.app.state.db.report(user["id"],target_id,payload.reason,request.app.state.settings.report_threshold)
    return {"ok":True}
