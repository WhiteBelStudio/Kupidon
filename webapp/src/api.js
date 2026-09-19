function getTelegramInitData(){
  const tg=window.Telegram?.WebApp;
  if(!tg) return "";
  // ready() is safe to call repeatedly and makes Telegram finish preparing
  // the WebApp object before we read initData.
  try{tg.ready();}catch(_){}
  return tg.initData || "";
}

function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms));}

export async function api(path,options={}){
  const headers=new Headers(options.headers||{});

  // Telegram WebApp can expose initData a little after the JS bundle starts.
  // Wait long enough to avoid a race on slower Telegram clients.
  let initData=getTelegramInitData();
  for(let i=0;i<20 && !initData;i+=1){
    await sleep(100);
    initData=getTelegramInitData();
  }

  if(initData){
    // Keep the existing custom header and also use the standard Authorization
    // header. The latter is more reliably preserved by hosted proxies/rewrites.
    headers.set("X-Telegram-Init-Data",initData);
    headers.set("Authorization",`tma ${initData}`);
  }

  const devId=import.meta.env.VITE_DEV_TELEGRAM_ID;
  if(!initData && devId) headers.set("X-Dev-Telegram-Id",devId);

  const response=await fetch(path,{...options,headers});
  if(!response.ok){
    const body=await response.json().catch(()=>({}));
    const detail=body.detail||"Ошибка запроса";
    if(response.status===401 && detail==="Telegram authorization required"){
      throw new Error("Telegram не передал данные Mini App. Закрой Mini App и открой его заново через кнопку бота.");
    }
    throw new Error(detail);
  }
  return response.json();
}
