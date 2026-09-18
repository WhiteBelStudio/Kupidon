const API_URL=(import.meta.env.VITE_API_URL||"").replace(/\/$/,"");
export async function api(path,options={}){
  const tg=window.Telegram?.WebApp;
  const headers=new Headers(options.headers||{});
  if(tg?.initData) headers.set("X-Telegram-Init-Data",tg.initData);
  const devId=import.meta.env.VITE_DEV_TELEGRAM_ID;
  if(!tg?.initData&&devId) headers.set("X-Dev-Telegram-Id",devId);
  const response=await fetch(API_URL+path,{...options,headers});
  if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail||"Ошибка запроса");}
  return response.json();
}
