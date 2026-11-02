import {Container,getContainer} from '@cloudflare/containers';
interface Env { ASSETS:Fetcher; LAB:DurableObjectNamespace<EvaluationContainer> }
const securityHeaders={
 'X-Content-Type-Options':'nosniff',
 'Referrer-Policy':'strict-origin-when-cross-origin',
 'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self' https://tedt.org https://*.tedt.org",
};
export class EvaluationContainer extends Container {
 defaultPort=8000;
 sleepAfter='2m';
 envVars={EVAL_LAB_HOSTED:'1',EVAL_LAB_DATA_DIR:'/app/data'};
 async onActivityExpired():Promise<void>{
  try{
   const r=await this.containerFetch('http://container/api/health');
   const state=await r.json() as {active_runs:number};
   if(state.active_runs>0){this.renewActivityTimeout();return;}
  }catch{}
  await this.stop();
 }
}
export default {
 async fetch(request:Request,env:Env):Promise<Response>{
  const url=new URL(request.url);
  let response:Response;
  if(url.pathname.startsWith('/api/')){
   const allowed=(request.method==='GET'&&url.pathname==='/api/health')||
    (request.method==='POST'&&['/api/connections/test','/api/runs'].includes(url.pathname));
   if(!allowed)return Response.json({detail:'Unknown evaluation API operation.'},{status:404});
   const length=Number(request.headers.get('content-length')||0);
   if(length>65536)return Response.json({detail:'Request exceeds the 64 KiB limit.'},{status:413});
   try{
    response=await getContainer(env.LAB,'shared-demo-v1').fetch(request);
   }catch{
    response=Response.json({detail:'The live evaluation service is starting or unavailable. Replay remains available. Try live mode again shortly.'},{status:503});
   }
  }else{
   response=await env.ASSETS.fetch(request);
  }
  const headers=new Headers(response.headers);
  for(const [key,value] of Object.entries(securityHeaders))headers.set(key,value);
  if(url.pathname.startsWith('/api/'))headers.set('Cache-Control','no-store');
  return new Response(response.body,{status:response.status,statusText:response.statusText,headers});
 }
};

