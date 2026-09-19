function getTelegramInitData(){
  const tg=window.Telegram?.WebApp;
  return tg?.initData || "";
}

function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms));}

export async function api(path,options={}){
  const headers=new Headers(options.headers||{});

  // Telegram may finish initializing WebApp a moment after the React bundle starts.
  // Retry briefly so saving a profile never races Telegram initialization.
  let initData=getTelegramInitData();
  if(!initData){
    for(let i=0;i<10 && !initData;i+=1){
      await sleep(100);
      initData=getTelegramInitData();
    }
  }

  if(initData) headers.set("X-Telegram-Init-Data",initData);

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
