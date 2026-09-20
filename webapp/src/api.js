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
  const initData=getTelegramInitData();

  if(initData){
    headers.set("X-Telegram-Init-Data",initData);
    headers.set("Authorization",`tma ${initData}`);
  }else{
    headers.set("X-Guest-Id",getGuestId());
  }

  const devId=import.meta.env.VITE_DEV_TELEGRAM_ID;
  if(!initData && devId) headers.set("X-Dev-Telegram-Id",devId);

  const controller=new AbortController();
  const externalSignal=options.signal;
  const timeoutMs=Number(options.timeoutMs || 10000);
  const timer=setTimeout(()=>controller.abort(),timeoutMs);

  if(externalSignal){
    if(externalSignal.aborted) controller.abort();
    else externalSignal.addEventListener("abort",()=>controller.abort(),{once:true});
  }

  const requestOptions={...options,headers,signal:controller.signal};
  delete requestOptions.timeoutMs;

  try{
    const response=await fetch(path,requestOptions);
    if(!response.ok){
      const body=await response.json().catch(()=>({}));
      throw new Error(body.detail||`Ошибка запроса (${response.status})`);
    }
    return response.json();
  }catch(error){
    if(error?.name==="AbortError"){
      throw new Error("Сервер отвечает слишком долго. Попробуйте ещё раз.");
    }
    throw error;
  }finally{
    clearTimeout(timer);
  }
}
