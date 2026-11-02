import {describe,it,expect} from 'vitest';
import {embedCode,parentOrigin,validateDistribution} from './portability';
describe('portable navigation',()=>{
 it('accepts explicit origins and rejects paths, credentials, wildcards, and scripts',()=>{
  expect(parentOrigin('?parent_origin=https%3A%2F%2Fblog.example')).toBe('https://blog.example');
  for(const value of ['https://blog.example/path','https://user:pass@blog.example','*','javascript:alert(1)','https://blog.example/'])expect(parentOrigin('?parent_origin='+encodeURIComponent(value))).toBeNull();
  expect(parentOrigin('')).toBeNull();
 });
 it('uses the current installation subpath for embeds',()=>{
  expect(embedCode('https://lab.example/course/?embed=1#lesson-2','https://blog.example')).toContain('https://lab.example/course/?embed=1&amp;parent_origin=https%3A%2F%2Fblog.example');
 });
 it('rejects remote and traversal download targets',()=>{
  const valid={schema_version:'1.0' as const,version:'1.1.0',downloads:[{edition:'react' as const,href:'./downloads/react.zip'}]};
  expect(validateDistribution(valid)).toEqual(valid);
  for(const href of ['https://remote.example/file.zip','//remote.example/file.zip','./../file.zip','./downloads/../../file.zip'])expect(()=>validateDistribution({...valid,downloads:[{edition:'react',href}]})).toThrow();
 });
});
