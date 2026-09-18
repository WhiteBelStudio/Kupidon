import {useEffect,useState} from "react";
import {api} from "./api";
import {initTelegram} from "./telegram";

const empty={age:14,city:"Белореченск",gender:"male",target_gender:"any",bio:"",interests:""};

function Photo({profile}){
  if(!profile?.photo_url&&!profile?.photo_path) return <div className="photo-placeholder">👤</div>;
  const src=profile.photo_url||(import.meta.env.VITE_API_URL+"/media/"+profile.photo_path);
  return <img className="profile-photo" src={src} alt=""/>;
}

function ProfileForm({profile,onSaved}){
  const [form,setForm]=useState(profile||empty); const [saving,setSaving]=useState(false); const [message,setMessage]=useState("");
  useEffect(()=>setForm(profile||empty),[profile]);
  const update=(k,v)=>setForm(x=>({...x,[k]:v}));
  async function save(e){e.preventDefault();setSaving(true);setMessage("");try{const r=await api("/api/profile",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(form)});onSaved(r.profile);setMessage("Профиль сохранён");}catch(e){setMessage(e.message)}finally{setSaving(false)}}
  async function upload(file){if(!file)return;const body=new FormData();body.append("file",file);try{await api("/api/profile/photo",{method:"POST",body});const r=await api("/api/profile");onSaved(r.profile);setMessage("Фото обновлено")}catch(e){setMessage(e.message)}}
  return <form className="panel" onSubmit={save}>
    <div className="avatar"><Photo profile={form}/></div>
    <label className="upload">📷 Добавить фото<input type="file" accept="image/*" onChange={e=>upload(e.target.files?.[0])}/></label>
    <label>Возраст<select value={form.age} onChange={e=>update("age",Number(e.target.value))}>{Array.from({length:12},(_,i)=>14+i).map(a=><option key={a}>{a}</option>)}</select></label>
    <label>Город<select value={form.city} onChange={e=>update("city",e.target.value)}><option>Белореченск</option></select></label>
    <label>Я<select value={form.gender} onChange={e=>update("gender",e.target.value)}><option value="male">👨 парень</option><option value="female">👩 девушка</option></select></label>
    <label>Хочу находить<select value={form.target_gender} onChange={e=>update("target_gender",e.target.value)}><option value="female">девушек</option><option value="male">парней</option><option value="any">всё равно</option></select></label>
    <label>О себе<textarea maxLength="1000" value={form.bio} onChange={e=>update("bio",e.target.value)} placeholder="Расскажи о себе..."/></label>
    <label>Интересы<input maxLength="500" value={form.interests} onChange={e=>update("interests",e.target.value)} placeholder="Игры, музыка, спорт..."/></label>
    <button className="primary" disabled={saving}>{saving?"Сохраняем...":"Сохранить профиль"}</button>
    {message&&<div className="notice">{message}</div>}
  </form>;
}

function Search(){
  const [profiles,setProfiles]=useState([]),[index,setIndex]=useState(0),[message,setMessage]=useState("");
  async function load(){try{const r=await api("/api/search");setProfiles(r.profiles);setIndex(0);setMessage(r.profiles.length?"":"Пока новых профилей нет.")}catch(e){setMessage(e.message)}}
  useEffect(()=>{load()},[]);
  async function react(action){const p=profiles[index];if(!p)return;try{const r=await api("/api/users/"+p.user_id+"/reaction",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action})});if(r.matched)setMessage("🤝 Взаимный интерес к дружбе!");setIndex(x=>x+1)}catch(e){setMessage(e.message)}}
  async function safety(action){const p=profiles[index];if(!p)return;if(action==="block"){await api("/api/users/"+p.user_id+"/block",{method:"POST"});setIndex(x=>x+1)}else{const reason=window.prompt("Причина жалобы:");if(!reason)return;await api("/api/users/"+p.user_id+"/report",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({reason})});setIndex(x=>x+1);setMessage("Жалоба отправлена модерации.")}}
  const p=profiles[index]; if(!p)return <div className="empty">{message||"Загрузка..."}</div>;
  return <div className="search"><article className="card"><Photo profile={p}/><div className="card-body"><h2>{p.first_name}, {p.age}</h2><div className="muted">{p.city}</div>{p.bio&&<p>{p.bio}</p>}{p.interests&&<div className="chips">{p.interests.split(",").map(x=><span key={x}>{x.trim()}</span>)}</div>}</div></article><div className="actions"><button className="secondary" onClick={()=>react("skip")}>⏭ Пропустить</button><button className="primary" onClick={()=>react("like")}>🤝 Познакомиться</button></div><div className="safety-actions"><button onClick={()=>safety("block")}>🚫 Заблокировать</button><button onClick={()=>safety("report")}>⚠️ Пожаловаться</button></div>{message&&<div className="notice">{message}</div>}</div>;
}

function Matches(){
  const [matches,setMatches]=useState([]);
  useEffect(()=>{api("/api/matches").then(r=>setMatches(r.matches)).catch(()=>{})},[]);
  return <div className="panel"><h2>🤝 Совпадения</h2>{matches.length===0?<div className="empty">Пока нет взаимных совпадений.</div>:matches.map(m=><div className="match" key={m.id}><div className="mini-avatar"><Photo profile={m}/></div><div><b>{m.first_name}, {m.age}</b><div className="muted">{m.city}</div></div></div>)}</div>;
}

export default function App(){
  const [tab,setTab]=useState("search"),[profile,setProfile]=useState(null),[error,setError]=useState("");
  useEffect(()=>{initTelegram();api("/api/profile").then(r=>setProfile(r.profile)).catch(e=>setError(e.message))},[]);
  if(error)return <main className="app"><div className="panel"><h1>КУПИДОН</h1><p>{error}</p><p className="muted">Открой Mini App через Telegram.</p></div></main>;
  return <main className="app"><header><div><div className="brand">КУПИДОН</div><div className="subtitle">друзья и общение</div></div></header><section className="content">{!profile?<ProfileForm profile={null} onSaved={setProfile}/>:tab==="search"?<Search/>:tab==="matches"?<Matches/>:<ProfileForm profile={profile} onSaved={setProfile}/>}</section><nav className="bottom-nav"><button className={tab==="search"?"active":""} onClick={()=>setTab("search")}>🔎<span>Поиск</span></button><button className={tab==="matches"?"active":""} onClick={()=>setTab("matches")}>🤝<span>Совпадения</span></button><button className={tab==="profile"?"active":""} onClick={()=>setTab("profile")}>👤<span>Профиль</span></button></nav></main>;
}
