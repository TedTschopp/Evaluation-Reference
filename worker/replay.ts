interface Env {ASSETS:Fetcher}
export default {
 async fetch(request:Request,env:Env):Promise<Response>{
  if(new URL(request.url).pathname.startsWith('/api/'))return Response.json({detail:'The live evaluation service has not been deployed. The complete replay is available.'},{status:503,headers:{'Cache-Control':'no-store'}});
  const r=await env.ASSETS.fetch(request);
  const headers=new Headers(r.headers);
  headers.set('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self' https://tedt.org https://*.tedt.org");
  headers.set('X-Content-Type-Options','nosniff');
  return new Response(r.body,{status:r.status,headers});
 }
};

