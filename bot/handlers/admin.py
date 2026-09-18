from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
router=Router()

@router.message(Command("admin"))
async def admin_panel(message:Message,db,settings):
    if message.from_user.id not in settings.admin_id_set:
        await message.answer("⛔ Доступ запрещён.")
        return
    reports=await db.get_open_reports()
    text=f"⚙️ <b>Панель администратора</b>\n\nОткрытых жалоб: <b>{len(reports)}</b>"
    for item in reports[:10]:
        text+=f"\n#{item['id']} — {item['reported_name']}: {item['reason'][:120]}"
    await message.answer(text)
