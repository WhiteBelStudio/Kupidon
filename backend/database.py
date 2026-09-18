from pathlib import Path
from typing import Any
import aiosqlite

class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            schema = Path(__file__).resolve().parents[1] / "database" / "migrations" / "001_initial.sql"
            await db.executescript(schema.read_text(encoding="utf-8"))
            await db.commit()

    async def _one(self, query: str, params: tuple[Any, ...] = ()) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(query, params)
            row = await cur.fetchone()
            return dict(row) if row else None

    async def _all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(query, params)
            return [dict(row) for row in await cur.fetchall()]

    async def upsert_user(self, telegram_id: int, username: str | None, first_name: str) -> dict:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO users(telegram_id, username, first_name) VALUES(?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name""",
                (telegram_id, username, first_name),
            )
            await db.commit()
        return await self.get_user(telegram_id)

    async def get_user(self, telegram_id: int) -> dict | None:
        return await self._one("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))

    async def get_user_by_id(self, user_id: int) -> dict | None:
        return await self._one("SELECT * FROM users WHERE id=?", (user_id,))

    async def get_profile(self, user_id: int) -> dict | None:
        return await self._one(
            """SELECT p.*, u.username, u.first_name,
            (SELECT path FROM profile_photos pp WHERE pp.user_id=p.user_id AND pp.is_primary=1 ORDER BY pp.id DESC LIMIT 1) photo_path
            FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=?""",
            (user_id,),
        )

    async def save_profile(self, user_id: int, data: dict) -> dict:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO profiles(user_id,age,city,gender,target_gender,bio,interests)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET age=excluded.age,city=excluded.city,
                gender=excluded.gender,target_gender=excluded.target_gender,bio=excluded.bio,
                interests=excluded.interests,is_active=1,updated_at=CURRENT_TIMESTAMP""",
                (user_id,data["age"],data["city"],data["gender"],data["target_gender"],data.get("bio",""),data.get("interests","")),
            )
            await db.commit()
        return await self.get_profile(user_id)

    async def set_photo(self, user_id: int, path: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE profile_photos SET is_primary=0 WHERE user_id=?", (user_id,))
            await db.execute("INSERT INTO profile_photos(user_id,path,is_primary) VALUES(?,?,1)", (user_id,path))
            await db.commit()

    async def search_profiles(self, user_id: int, limit: int = 20) -> list[dict]:
        profile = await self.get_profile(user_id)
        if not profile:
            return []
        target = profile["target_gender"]
        clause = "" if target == "any" else "AND p.gender=?"
        params: list[Any] = [user_id]
        if target != "any":
            params.append(target)
        params += [user_id,user_id,user_id,limit]
        return await self._all(
            f"""SELECT p.user_id,p.age,p.city,p.gender,p.bio,p.interests,u.username,u.first_name,
            (SELECT path FROM profile_photos pp WHERE pp.user_id=p.user_id AND pp.is_primary=1 ORDER BY pp.id DESC LIMIT 1) photo_path
            FROM profiles p JOIN users u ON u.id=p.user_id
            WHERE p.user_id!=? AND p.is_active=1 AND u.is_blocked=0 {clause}
            AND NOT EXISTS (SELECT 1 FROM blocks b WHERE (b.blocker_id=? AND b.blocked_id=p.user_id) OR (b.blocker_id=p.user_id AND b.blocked_id=?))
            AND NOT EXISTS (SELECT 1 FROM reactions r WHERE r.from_user_id=? AND r.to_user_id=p.user_id)
            ORDER BY RANDOM() LIMIT ?""",
            tuple(params),
        )

    async def react(self, from_id: int, to_id: int, action: str) -> tuple[bool,int|None]:
        if action not in {"like","skip"} or from_id == to_id:
            raise ValueError("Invalid reaction")
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO reactions(from_user_id,to_user_id,action) VALUES(?,?,?)
                ON CONFLICT(from_user_id,to_user_id) DO UPDATE SET action=excluded.action,created_at=CURRENT_TIMESTAMP""",
                (from_id,to_id,action),
            )
            match_id = None
            if action == "like":
                cur = await db.execute("SELECT action FROM reactions WHERE from_user_id=? AND to_user_id=?", (to_id,from_id))
                reciprocal = await cur.fetchone()
                if reciprocal and reciprocal[0] == "like":
                    a,b = sorted((from_id,to_id))
                    await db.execute("INSERT OR IGNORE INTO matches(user1_id,user2_id) VALUES(?,?)", (a,b))
                    cur = await db.execute("SELECT id FROM matches WHERE user1_id=? AND user2_id=?", (a,b))
                    row = await cur.fetchone()
                    match_id = row[0] if row else None
            await db.commit()
        return match_id is not None, match_id

    async def get_matches(self, user_id: int) -> list[dict]:
        return await self._all(
            """SELECT m.id,m.created_at,
            CASE WHEN m.user1_id=? THEN m.user2_id ELSE m.user1_id END other_id,
            u.first_name,u.username,p.age,p.city,p.bio,p.interests,
            (SELECT path FROM profile_photos pp WHERE pp.user_id=u.id AND pp.is_primary=1 ORDER BY pp.id DESC LIMIT 1) photo_path
            FROM matches m JOIN users u ON u.id=CASE WHEN m.user1_id=? THEN m.user2_id ELSE m.user1_id END
            LEFT JOIN profiles p ON p.user_id=u.id WHERE m.user1_id=? OR m.user2_id=? ORDER BY m.id DESC""",
            (user_id,user_id,user_id,user_id),
        )

    async def block(self, blocker_id: int, blocked_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR IGNORE INTO blocks(blocker_id,blocked_id) VALUES(?,?)", (blocker_id,blocked_id))
            await db.execute("UPDATE profiles SET is_active=0 WHERE user_id=?", (blocked_id,))
            await db.commit()

    async def report(self, reporter_id: int, reported_id: int, reason: str, threshold: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO reports(reporter_id,reported_id,reason) VALUES(?,?,?)", (reporter_id,reported_id,reason[:1000]))
            cur = await db.execute("SELECT COUNT(*) FROM reports WHERE reported_id=? AND status='open'", (reported_id,))
            count = (await cur.fetchone())[0]
            if count >= threshold:
                await db.execute("UPDATE profiles SET is_active=0 WHERE user_id=?", (reported_id,))
            await db.commit()

    async def get_open_reports(self, limit: int = 50) -> list[dict]:
        return await self._all(
            """SELECT r.*,u2.first_name reported_name FROM reports r
            JOIN users u1 ON u1.id=r.reporter_id JOIN users u2 ON u2.id=r.reported_id
            WHERE r.status='open' ORDER BY r.id DESC LIMIT ?""", (limit,),
        )
