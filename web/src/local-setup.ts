import type {Connection} from './types';

export interface ServiceHealth {version:string;hosted:boolean;protocols:string[]}
export const serviceUnavailable='The live evaluation service is unavailable at this address. Start the bundled Python service, then open its printed URL.';

export async function checkService(signal?:AbortSignal):Promise<ServiceHealth>{
 const response=await fetch('./api/health',{signal});
 if(!response.ok||!response.headers.get('content-type')?.includes('application/json'))throw Error(serviceUnavailable);
 const value=await response.json();
 if(value.status!=='ok'||typeof value.version!=='string'||typeof value.hosted!=='boolean'||!Array.isArray(value.protocols))throw Error(serviceUnavailable);
 return value;
}

export async function connectionResponse(response:Response):Promise<{connected:boolean;tools:boolean;message:string}>{
 if(!response.headers.get('content-type')?.includes('application/json'))throw Error(serviceUnavailable);
 const value=await response.json();
 if(!response.ok)throw Error(value.detail||value.message||'The connection test failed. Check the model URL, model name, and authentication.');
 return value;
}

export function localOllama(name='My agent'):Connection{
 return {definition:{schema_version:'1.0',id:name==='My agent'?'my-agent':'my-judge',name,protocol:'ollama',base_url:'http://localhost:11434',model:'llama3.2:3b',authentication:{type:'none'},generation:{temperature:0,max_output_tokens:1200,timeout_seconds:120,json_schema:true},capabilities:{tools:null,streaming:null}}};
}

export function connectionComplete(connection:Connection):boolean{
 try{const url=new URL(connection.definition.base_url);return ['http:','https:'].includes(url.protocol)&&!!connection.definition.model.trim()&&(connection.definition.authentication.type==='none'||!!connection.api_key?.trim());}catch{return false;}
}
