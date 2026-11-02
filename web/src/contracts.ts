import type { Case, CaseResult, Decision, ReleasePolicy, RunBundle } from './types';
export const defaultPolicy:ReleasePolicy={id:'teaching-default-v1',minimum_pass_rate:.9,maximum_critical_failures:0,require_complete:true};
export function decideRelease(results:CaseResult[],policy:ReleasePolicy,expectedTotal=results.length):Decision {
 const total=Math.max(results.length,expectedTotal);
 const failed=(r:CaseResult)=>r.status==='fail'||r.grades.some(g=>g.required&&g.status==='fail');
 const incomplete=(r:CaseResult)=>r.status==='error'||r.status==='unresolved'||r.grades.some(g=>g.required&&['error','not_assessed'].includes(g.status));
 const passed=results.filter(r=>r.status==='pass'&&!failed(r)&&!incomplete(r)).length;
 const critical=results.filter(r=>r.critical&&failed(r)).length;
 const unresolved=results.filter(incomplete).length+total-results.length;
 const rate=total?passed/total:0; const reasons:string[]=[];
 if(!total)reasons.push('No cases have been evaluated.');
 if(critical>policy.maximum_critical_failures)reasons.push(critical+' critical case(s) failed; policy allows '+policy.maximum_critical_failures+'.');
 if(policy.require_complete&&unresolved)reasons.push(unresolved+' case(s) have required evaluations unresolved or errored.');
 if(rate<policy.minimum_pass_rate)reasons.push(passed+'/'+total+' cases passed; the required rate is '+Math.round(policy.minimum_pass_rate*100)+'%.');
 return {verdict:reasons.length?'hold':'eligible',passed,total,pass_rate:rate,critical_failures:critical,unresolved,reasons:reasons.length?reasons:['The tested cases meet this policy. This is bounded evidence, not a guarantee.'],policy};
}
export function validateBundle(value:unknown,knownCases:Pick<Case,'id'|'critical'|'expected_disposition'>[]):RunBundle {
 if(!value||typeof value!=='object')throw Error('Choose a RunBundle JSON object.');
 const b=value as RunBundle;
 if(b.schema_version!=='1.0'||!Array.isArray(b.results)||b.results.length>36||![12,36].includes(b.expected_results)||b.expected_results<b.results.length)throw Error('The release denominator must cover the complete twelve-case suite.');
 if(typeof b.id!=='string'||!b.versions||typeof b.provenance!=='string'||!['replay','live'].includes(b.mode))throw Error('RunBundle metadata is incomplete.');
 const identities=new Set<string>(),criteria=['task_intent','citation_provenance','evidence_boundary','scope_alignment','appropriate_response'];
 const reps=b.expected_results/12;
 for(const r of b.results){
  const task=knownCases.find(c=>c.id===r.case_id);
  if(!task||!r.answer||typeof r.answer.text!=='string'||r.answer.text.length>30000||!Array.isArray(r.answer.citations)||!r.answer.citations.every(x=>typeof x==='string')||!Array.isArray(r.grades)||!Array.isArray(r.events)||r.events.length>1000)throw Error('A case, answer, grade, or trace is invalid.');
  if(!['answer','clarify','insufficient_evidence'].includes(r.answer.disposition)||!['authored_fixture','captured_model_run'].includes(r.source_kind)||!['pass','fail','error','unresolved'].includes(r.status))throw Error('A result contains an unsupported state.');
  const identity=r.case_id+':'+r.repetition;
  if(!Number.isInteger(r.repetition)||r.repetition<1||r.repetition>reps||identities.has(identity))throw Error('Duplicate or invalid case/repetition identity.');
  identities.add(identity);
  if(r.critical!==task.critical)throw Error('Critical-case metadata does not match the case manifest.');
  if(r.status==='error'){if(!r.error||typeof r.error!=='string')throw Error('An execution error needs an explanation.');continue;}
  const names=new Set(r.grades.map(g=>g.name));
  if(names.size!==r.grades.length||criteria.some(n=>!names.has(n)))throw Error('Required canonical evaluation criteria are missing or duplicated.');
  const factual=r.answer.disposition==='answer',applicable=factual&&task.expected_disposition==='answer';
  for(const g of r.grades){
   if(typeof g.name!=='string'||typeof g.label!=='string'||typeof g.reason!=='string'||typeof g.required!=='boolean'||!['pass','fail','error','not_assessed','not_applicable'].includes(g.status))throw Error('An evaluation result has an invalid contract.');
   if(criteria.includes(g.name)){
    const na=(g.name==='scope_alignment'&&!applicable)||(g.name==='citation_provenance'&&!factual&&!r.answer.citations.length);
    if(g.kind!=='deterministic'||g.required===na||(g.status==='not_applicable')!==na)throw Error('Criterion applicability or required status was altered.');
   }
  }
  const judge=r.grades.find(g=>g.name==='semantic_judge');
  if(b.judge_endpoint&&(!judge||!judge.required))throw Error('A configured AI judge is a required assessment.');
  const required=r.grades.filter(g=>g.required);
  const computed=required.some(g=>g.status==='fail')?'fail':!required.length||required.some(g=>g.status==='error'||g.status==='not_assessed')?'unresolved':'pass';
  if(r.status!==computed)throw Error('A case status disagrees with its required evaluations.');
 }
 // Counters and decisions from imported files are not trusted.
 const p=b.decision?.policy;
 if(!p||typeof p.id!=='string'||typeof p.require_complete!=='boolean'||!Number.isFinite(p.minimum_pass_rate)||p.minimum_pass_rate<0||p.minimum_pass_rate>1||!Number.isInteger(p.maximum_critical_failures)||p.maximum_critical_failures<0||p.maximum_critical_failures>12)throw Error('The release policy is invalid.');
 return {...b,judge_calibration:b.judge_calibration||[],decision:decideRelease(b.results,p,b.expected_results)};
}
export function downloadJson(name:string,value:unknown) {
 const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)+'\n'],{type:'application/json'}));
 const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export async function readEvents(response:Response,onEvent:(event:Record<string,unknown>)=>void) {
 if(!response.ok){let message='The live service is unavailable.';try{const v=await response.json();message=v.detail||v.message||message;}catch{}throw Error(message);}
 if(!response.body)throw Error('The live service returned no event stream.');
 const reader=response.body.getReader();const decoder=new TextDecoder();let buffer='';
 try {
  while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let pos;
   while((pos=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,pos).trim();buffer=buffer.slice(pos+1);if(line)onEvent(JSON.parse(line));}
   if(buffer.length>16_000_000)throw Error('The live event exceeded the import limit.');
  }
  buffer+=decoder.decode();if(buffer.trim())onEvent(JSON.parse(buffer));
 } finally {reader.releaseLock();}
}

