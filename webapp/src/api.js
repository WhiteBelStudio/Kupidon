export async function api(path,options={}){
  const tg=window.Telegram?.WebApp;
  const headers=new Headers(options.headers||{});
  if(tg?.initData) headers.set("X-Telegram-Init-Data",tg.initData);
  const devId=import.meta.env.VITE_DEV_TELEGRAM_ID;
  if(!tg?.initData&&devId) headers.set("X-Dev-Telegram-Id",devId);

  // Production: API is served through the same KUPIDON Vercel origin.
  // This avoids requiring VITE_API_URL in the Mini App.
  const response=await fetch(path,{...options,headers});
  if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail||"Ошибка запроса");}
  return response.json();
}
