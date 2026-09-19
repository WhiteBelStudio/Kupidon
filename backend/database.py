from pathlib import Path
from typing import Any
import aiosqlite
import asyncpg

class Database:
    def __init__(self, url: str = "", path: str = "data/kupidon.db"):
        self.url=url.strip()
        self.path=path
        self.pool=None

    async def init(self):
        if self.url:
            self.pool=await asyncpg.create_pool(self.url,min_size=1,max_size=5,command_timeout=15)
            schema=(Path(__file__).resolve().parents[1]/"database"/"migrations"/"002_postgres.sql").read_text(encoding="utf-8")
            async with self.pool.acquire() as conn: await conn.execute(schema)
            return
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        schema=(Path(__file__).resolve().parents[1]/"database"/"migrations"/"001_initial.sql").read_text(encoding="utf-8")
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(schema); await db.commit()

    async def close(self):
        if self.pool: await self.pool.close(); self.pool=None

    async def _one(self,q,params=()):
        if self.pool:
            async with self.pool.acquire() as c:
                r=await c.fetchrow(q,*params); return dict(r) if r else None
        async with aiosqlite.connect(self.path) as db:
            db.row_factory=aiosqlite.Row
            c=await db.execute(q,params); r=await c.fetchone(); return dict(r) if r else None

    async def _all(self,q,params=()):
        if self.pool:
            async with self.pool.acquire() as c: return [dict(r) for r in await c.fetch(q,*params)]
        async with aiosqlite.connect(self.path) as db:
            db.row_factory=aiosqlite.Row
            c=await db.execute(q,params); return [dict(r) for r in await c.fetchall()]

    async def upsert_user(self,telegram_id,username,first_name):
        if self.pool:
            async with self.pool.acquire() as c:
                await c.execute("""INSERT INTO users(telegram_id,username,first_name) VALUES($1,$2,$3)
                ON CONFLICT(telegram_id) DO UPDATE SET username=EXCLUDED.username,first_name=EXCLUDED.first_name""",telegram_id,username,first_name)
        else:
            async with aiosqlite.connect(self.path) as db:
                await db.execute("""INSERT INTO users(telegram_id,username,first_name) VALUES(?,?,?)
                ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name""",(telegram_id,username,first_name)); await db.commit()
        return await self.get_user(telegram_id)

    async def get_user(self,telegram_id):
        return await self._one("SELECT * FROM users WHERE telegram_id=$1" if self.pool else "SELECT * FROM users WHERE telegram_id=?",(telegram_id,))

    async def get_user_by_id(self,user_id):
        return await self._one("SELECT * FROM users WHERE id=$1" if self.pool else "SELECT * FROM users WHERE id=?",(user_id,))

    async def get_profile(self,user_id):
        q="""SELECT p.*,u.username,u.first_name,
        (SELECT path FROM profile_photos pp WHERE pp.user_id=p.user_id AND pp.is_primary=TRUE ORDER BY pp.id DESC LIMIT 1) photo_path
        FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=$1"""
        if not self.pool: q=q.replace("$1","?").replace("TRUE","1")
        return await self._one(q,(user_id,))

    async def save_profile(self,user_id,data):
        if self.pool:
            async with self.pool.acquire() as c:
                await c.execute("""INSERT INTO profiles(user_id,age,city,gender,target_gender,bio,interests)
                VALUES($1,$2,$3,$4,$5,$6,$7) ON CONFLICT(user_id) DO UPDATE SET
                age=EXCLUDED.age,city=EXCLUDED.city,gender=EXCLUDED.gender,target_gender=EXCLUDED.target_gender,
                bio=EXCLUDED.bio,interests=EXCLUDED.interests,is_active=TRUE,updated_at=CURRENT_TIMESTAMP""",
                user_id,data["age"],data["city"],data["gender"],data["target_gender"],data.get("bio",""),data.get("interests",""))
        else:
            async with aiosqlite.connect(self.path) as db:
                await db.execute("""INSERT INTO profiles(user_id,age,city,gender,target_gender,bio,interests)
                VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET age=excluded.age,city=excluded.city,
                gender=excluded.gender,target_gender=excluded.target_gender,bio=excluded.bio,interests=excluded.interests,
                is_active=1,updated_at=CURRENT_TIMESTAMP""",(user_id,data["age"],data["city"],data["gender"],data["target_gender"],data.get("bio",""),data.get("interests",""))); await db.commit()
        return await self.get_profile(user_id)

    async def set_photo(self,user_id,path,data,content_type):
        if self.pool:
            async with self.pool.acquire() as c:
                async with c.transaction():
                    await c.execute("UPDATE profile_photos SET is_primary=FALSE WHERE user_id=$1",user_id)
                    await c.execute("INSERT INTO profile_photos(user_id,path,content_type,data,is_primary) VALUES($1,$2,$3,$4,TRUE)",user_id,path,content_type,data)
        else:
            async with aiosqlite.connect(self.path) as db:
                await db.execute("UPDATE profile_photos SET is_primary=0 WHERE user_id=?",(user_id,))
                await db.execute("INSERT INTO profile_photos(user_id,path,is_primary) VALUES(?,?,1)",(user_id,path)); await db.commit()

    async def get_photo(self,path):
        if not self.pool: return None
        async with self.pool.acquire() as c:
            r=await c.fetchrow("SELECT data,content_type FROM profile_photos WHERE path=$1",path)
            return dict(r) if r else None

    async def search_profiles(self,user_id,limit=20):
        p=await self.get_profile(user_id)
        if not p:return []
        target=p["target_gender"]
        if self.pool:
            if target=="any":
                q="""SELECT p.user_id,p.age,p.city,p.gender,p.bio,p.interests,u.username,u.first_name,
                (SELECT path FROM profile_photos pp WHERE pp.user_id=p.user_id AND pp.is_primary=TRUE ORDER BY pp.id DESC LIMIT 1) photo_path
                FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id!=$1 AND p.is_active=TRUE AND u.is_blocked=FALSE
                AND NOT EXISTS(SELECT 1 FROM blocks b WHERE (b.blocker_id=$1 AND b.blocked_id=p.user_id) OR (b.blocker_id=p.user_id AND b.blocked_id=$1))
                AND NOT EXISTS(SELECT 1 FROM reactions r WHERE r.from_user_id=$1 AND r.to_user_id=p.user_id)
                ORDER BY RANDOM() LIMIT $2"""
                return await self._all(q,(user_id,limit))
            q="""SELECT p.user_id,p.age,p.city,p.gender,p.bio,p.interests,u.username,u.first_name,
            (SELECT path FROM profile_photos pp WHERE pp.user_id=p.user_id AND pp.is_primary=TRUE ORDER BY pp.id DESC LIMIT 1) photo_path
            FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id!=$1 AND p.is_active=TRUE AND u.is_blocked=FALSE AND p.gender=$2
            AND NOT EXISTS(SELECT 1 FROM blocks b WHERE (b.blocker_id=$1 AND b.blocked_id=p.user_id) OR (b.blocker_id=p.user_id AND b.blocked_id=$1))
            AND NOT EXISTS(SELECT 1 FROM reactions r WHERE r.from_user_id=$1 AND r.to_user_id=p.user_id)
            ORDER BY RANDOM() LIMIT $3"""
            return await self._all(q,(user_id,target,limit))
        clause="" if target=="any" else "AND p.gender=?"; params=[user_id]
        if target!="any": params.append(target)
        params += [user_id,user_id,user_id,limit]
        return await self._all(f"""SELECT p.user_id,p.age,p.city,p.gender,p.bio,p.interests,u.username,u.first_name,
        (SELECT path FROM profile_photos pp WHERE pp.user_id=p.user_id AND pp.is_primary=1 ORDER BY pp.id DESC LIMIT 1) photo_path
        FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id!=? AND p.is_active=1 AND u.is_blocked=0 {clause}
        AND NOT EXISTS(SELECT 1 FROM blocks b WHERE (b.blocker_id=? AND b.blocked_id=p.user_id) OR (b.blocker_id=p.user_id AND b.blocked_id=?))
        AND NOT EXISTS(SELECT 1 FROM reactions r WHERE r.from_user_id=? AND r.to_user_id=p.user_id) ORDER BY RANDOM() LIMIT ?""",tuple(params))

    async def react(self,from_id,to_id,action):
        if action not in {"like","skip"} or from_id==to_id: raise ValueError("Invalid reaction")
        if self.pool:
            async with self.pool.acquire() as c:
                async with c.transaction():
                    await c.execute("""INSERT INTO reactions(from_user_id,to_user_id,action) VALUES($1,$2,$3)
                    ON CONFLICT(from_user_id,to_user_id) DO UPDATE SET action=EXCLUDED.action,created_at=CURRENT_TIMESTAMP""",from_id,to_id,action)
                    if action!="like": return False,None
                    r=await c.fetchrow("SELECT action FROM reactions WHERE from_user_id=$1 AND to_user_id=$2",to_id,from_id)
                    if not r or r["action"]!="like": return False,None
                    a,b=sorted((from_id,to_id))
                    r=await c.fetchrow("""INSERT INTO matches(user1_id,user2_id) VALUES($1,$2)
                    ON CONFLICT(user1_id,user2_id) DO UPDATE SET user1_id=EXCLUDED.user1_id RETURNING id""",a,b)
                    return True,int(r["id"])
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""INSERT INTO reactions(from_user_id,to_user_id,action) VALUES(?,?,?)
            ON CONFLICT(from_user_id,to_user_id) DO UPDATE SET action=excluded.action,created_at=CURRENT_TIMESTAMP""",(from_id,to_id,action))
            mid=None
            if action=="like":
                c=await db.execute("SELECT action FROM reactions WHERE from_user_id=? AND to_user_id=?",(to_id,from_id)); r=await c.fetchone()
                if r and r[0]=="like":
                    a,b=sorted((from_id,to_id)); await db.execute("INSERT OR IGNORE INTO matches(user1_id,user2_id) VALUES(?,?)",(a,b))
                    c=await db.execute("SELECT id FROM matches WHERE user1_id=? AND user2_id=?",(a,b)); r=await c.fetchone(); mid=r[0] if r else None
            await db.commit(); return mid is not None,mid

    async def get_matches(self,user_id):
        q="""SELECT m.id,m.created_at,CASE WHEN m.user1_id=$1 THEN m.user2_id ELSE m.user1_id END other_id,
        u.first_name,u.username,p.age,p.city,p.bio,p.interests,
        (SELECT path FROM profile_photos pp WHERE pp.user_id=u.id AND pp.is_primary=TRUE ORDER BY pp.id DESC LIMIT 1) photo_path
        FROM matches m JOIN users u ON u.id=CASE WHEN m.user1_id=$1 THEN m.user2_id ELSE m.user1_id END
        LEFT JOIN profiles p ON p.user_id=u.id WHERE m.user1_id=$1 OR m.user2_id=$1 ORDER BY m.id DESC"""
        if self.pool:return await self._all(q,(user_id,))
        q=q.replace("$1","?").replace("TRUE","1"); return await self._all(q,(user_id,user_id,user_id))
    
    async def block(self,blocker_id,blocked_id):
        if self.pool:
            async with self.pool.acquire() as c:
                async with c.transaction():
                    await c.execute("INSERT INTO blocks(blocker_id,blocked_id) VALUES($1,$2) ON CONFLICT DO NOTHING",blocker_id,blocked_id)
                    await c.execute("UPDATE profiles SET is_active=FALSE WHERE user_id=$1",blocked_id)
            return
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR IGNORE INTO blocks(blocker_id,blocked_id) VALUES(?,?)",(blocker_id,blocked_id)); await db.execute("UPDATE profiles SET is_active=0 WHERE user_id=?",(blocked_id,)); await db.commit()

    async def report(self,reporter_id,reported_id,reason,threshold):
        if self.pool:
            async with self.pool.acquire() as c:
                async with c.transaction():
                    await c.execute("INSERT INTO reports(reporter_id,reported_id,reason) VALUES($1,$2,$3)",reporter_id,reported_id,reason[:1000])
                    count=await c.fetchval("SELECT COUNT(*) FROM reports WHERE reported_id=$1 AND status='open'",reported_id)
                    if count>=threshold: await c.execute("UPDATE profiles SET is_active=FALSE WHERE user_id=$1",reported_id)
            return
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO reports(reporter_id,reported_id,reason) VALUES(?,?,?)",(reporter_id,reported_id,reason[:1000]))
            c=await db.execute("SELECT COUNT(*) FROM reports WHERE reported_id=? AND status='open'",(reported_id,)); count=(await c.fetchone())[0]
            if count>=threshold: await db.execute("UPDATE profiles SET is_active=0 WHERE user_id=?",(reported_id,))
            await db.commit()

    async def get_open_reports(self,limit=50):
        q="""SELECT r.*,u2.first_name AS reported_name FROM reports r JOIN users u1 ON u1.id=r.reporter_id JOIN users u2 ON u2.id=r.reported_id
        WHERE r.status='open' ORDER BY r.id DESC LIMIT $1"""
        if self.pool:return await self._all(q,(limit,))
        return await self._all(q.replace("$1","?"),(limit,))
