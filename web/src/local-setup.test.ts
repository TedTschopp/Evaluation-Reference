import {afterEach,describe,it,expect,vi} from 'vitest';
import {checkService,connectionComplete,connectionResponse,localOllama,serviceUnavailable} from './local-setup';
afterEach(()=>vi.unstubAllGlobals());
describe('first local setup',()=>{
 it('provides a usable key-free local connection',()=>{
  const local=localOllama();expect(connectionComplete(local)).toBe(true);expect(local.definition.protocol).toBe('ollama');expect(local.definition.base_url).toBe('http://localhost:11434');expect(local.definition.generation.timeout_seconds).toBe(120);expect(local.definition.generation.json_schema).toBe(true);expect(local.api_key).toBeUndefined();
  expect(connectionComplete({...local,definition:{...local.definition,base_url:'http'}})).toBe(false);
  expect(connectionComplete({...local,definition:{...local.definition,authentication:{type:'bearer'}}})).toBe(false);
 });
 it('distinguishes static servers and unknown JSON from a running service',async()=>{
  for(const response of [new Response('<html>not found</html>',{status:404}),new Response('{}',{headers:{'content-type':'application/json'}})]){
   vi.stubGlobal('fetch',vi.fn().mockResolvedValue(response));await expect(checkService()).rejects.toThrow(serviceUnavailable);
  }
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue(Response.json({status:'ok',version:'1.2.0',hosted:false,protocols:['ollama']})));
  expect((await checkService()).hosted).toBe(false);
 });
 it('turns static-server HTML into setup instructions and retains useful API errors',async()=>{
  await expect(connectionResponse(new Response('<!DOCTYPE html>',{status:501}))).rejects.toThrow(serviceUnavailable);
  await expect(connectionResponse(Response.json({message:'The model was not found.'},{status:400}))).rejects.toThrow('The model was not found.');
 });
});
