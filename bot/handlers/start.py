from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup,Message,WebAppInfo
router=Router()

def app_keyboard(url):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Открыть КУПИДОН",web_app=WebAppInfo(url=url))]])

@router.message(Command("start"))
async def start(message:Message,db,settings):
    user=await db.upsert_user(message.from_user.id,message.from_user.username,message.from_user.first_name or "Пользователь")
    profile=await db.get_profile(user["id"])
    if profile:
        text="👋 <b>С возвращением в КУПИДОН!</b>\n\nЗдесь можно находить друзей и общаться. КУПИДОН не предназначен для романтического или сексуального общения."
    else:
        text="👋 <b>Добро пожаловать в КУПИДОН!</b>\n\nСоздай профиль и находи друзей со схожими интересами. КУПИДОН не предназначен для романтического или сексуального общения."
    await message.answer(text,reply_markup=app_keyboard(settings.webapp_url))

@router.message(Command("help"))
async def help_command(message:Message,settings):
    await message.answer("КУПИДОН — приложение для поиска друзей и общения.",reply_markup=app_keyboard(settings.webapp_url))
