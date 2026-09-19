function getTelegramInitData(){
  const tg=window.Telegram?.WebApp;
  if(!tg) return "";
  try{tg.ready();}catch(_){}
  return tg.initData || "";
}

function getGuestId(){
  const key="kupidon_guest_id";
  try{
    let id=localStorage.getItem(key);
    if(!id){
      id=crypto.randomUUID();
      localStorage.setItem(key,id);
    }
    return id;
  }catch(_){
    return "browser-guest";
  }
}

export async function api(path,options={}){
  const headers=new Headers(options.headers||{});

  // Telegram identity is optional. If the app is opened in Telegram, keep
  // using its verified identity; otherwise use a persistent browser guest.
  const initData=getTelegramInitData();
  if(initData){
    headers.set("X-Telegram-Init-Data",initData);
    headers.set("Authorization",`tma ${initData}`);
  }else{
    headers.set("X-Guest-Id",getGuestId());
  }

  const devId=import.meta.env.VITE_DEV_TELEGRAM_ID;
  if(!initData && devId) headers.set("X-Dev-Telegram-Id",devId);

  const response=await fetch(path,{...options,headers});
  if(!response.ok){
    const body=await response.json().catch(()=>({}));
    throw new Error(body.detail||"Ошибка запроса");
  }
  return response.json();
}