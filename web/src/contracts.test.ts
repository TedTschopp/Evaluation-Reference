import {describe,it,expect} from 'vitest';
import {decideRelease,defaultPolicy,validateBundle,readEvents} from './contracts';
import type {Replays} from './types';
import replaysJson from '../public/data/replays.json';
import casesJson from '../public/data/cases.json';
const data=replaysJson as unknown as Replays;
describe('cross-language contracts',()=>{
 for(const profile of data.profiles)it('reproduces Python decision: '+profile.id,()=>{
  expect(decideRelease(profile.bundle.results,defaultPolicy,profile.bundle.expected_results)).toEqual(profile.bundle.decision);
 });
 it('holds a better-scoring critical failure',()=>{
  const candidate=data.profiles.find(p=>p.id==='candidate')!;
  expect(candidate.bundle.decision.passed).toBe(11);
  expect(decideRelease(candidate.bundle.results,defaultPolicy).verdict).toBe('hold');
 });
 it('does not accept fabricated aggregate counts',()=>{
  const b=structuredClone(data.profiles[1].bundle);b.decision.passed=12;b.decision.verdict='eligible';
  expect(validateBundle(b,casesJson.cases).decision.verdict).toBe('hold');
 });
 it('rejects a contradictory case status',()=>{
  const b=structuredClone(data.profiles[1].bundle);b.results.find(r=>r.status==='fail')!.status='pass';
  expect(()=>validateBundle(b,casesJson.cases)).toThrow();
 });
 it.each(['duplicate','critical','invented'])('rejects tampered imports: %s',(kind)=>{
  const b=structuredClone(data.profiles[2].bundle);
  if(kind==='duplicate')b.results=Array.from({length:12},()=>structuredClone(b.results[0]));
  if(kind==='critical')b.results.find(r=>r.critical)!.critical=false;
  if(kind==='invented')b.results[0].grades=[{name:'anything',label:'Anything',kind:'deterministic',status:'pass',required:true,reason:'Claimed',score:1,evidence_ids:[]}];
  expect(()=>validateBundle(b,casesJson.cases)).toThrow();
 });
 it('keeps a critical failure visible when a judge also errors',()=>{
  const b=structuredClone(data.profiles[1].bundle);
  const r=b.results.find(x=>x.critical)!;
  r.grades.push({name:'judge',label:'Judge',kind:'ai_judge',status:'error',required:true,reason:'Unavailable',score:null,evidence_ids:[]});
  const d=decideRelease(b.results,{...defaultPolicy,require_complete:false},12);
  expect(d.verdict).toBe('hold');expect(d.critical_failures).toBe(1);expect(d.unresolved).toBe(1);
 });
 it('holds a partial suite',()=>{
  expect(decideRelease([data.profiles[2].bundle.results[0]],defaultPolicy,12).unresolved).toBe(11);
 });
 it('parses split NDJSON records',async()=>{
  const stream=new ReadableStream({start(controller){controller.enqueue(new TextEncoder().encode('{"type":"sta'));controller.enqueue(new TextEncoder().encode('rted"}\n{"type":"complete"}\n'));controller.close();}});
  const events:unknown[]=[];await readEvents(new Response(stream),event=>events.push(event));
  expect(events).toEqual([{type:'started'},{type:'complete'}]);
 });
});

