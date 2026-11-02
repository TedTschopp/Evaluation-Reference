export type GradeStatus = 'pass'|'fail'|'error'|'not_assessed'|'not_applicable';
export interface Passage { id:string; document_id:string; label:string; text:string; ordinal:number }
export interface Document { id:string; title:string; date:string; source_url:string; text:string; sha256:string; annotations:string[]; passages:Passage[]; provenance:Record<string,unknown> }
export interface Corpus { schema_version:string; version:string; documents:Document[]; collections:{id:string;title:string;document_ids:string[]}[]; relationships:Record<string,string>[] }
export interface Case { id:string;family:string;title:string;question:string;expected_behavior:string;allowed_document_ids:string[];required_document_ids:string[];concepts:string[];expected_disposition:string;as_of:string|null;critical:boolean;reference_answer:string;reference_passage_ids:string[] }
export interface Grade {name:string;label:string;kind:'deterministic'|'ai_judge'|'weak_checker'|'reference';status:GradeStatus;required:boolean;reason:string;score:number|null;evidence_ids:string[]}
export interface TraceEvent {type:string;sequence:number;name?:string;arguments?:Record<string,unknown>;passage_ids?:string[];text?:string;citations?:string[];elapsed_ms?:number;message?:string}
export interface Answer {text:string;citations:string[];disposition:'answer'|'clarify'|'insufficient_evidence';as_of:string|null}
export interface CaseResult {case_id:string;repetition:number;profile:string;source_kind:'authored_fixture'|'captured_model_run';answer:Answer;events:TraceEvent[];messages:Record<string,unknown>[];grades:Grade[];status:'pass'|'fail'|'error'|'unresolved';critical:boolean;latency_ms:number|null;tokens:Record<string,number>|null;framework:Record<string,unknown>;error:string|null}
export interface ReleasePolicy {id:string;minimum_pass_rate:number;maximum_critical_failures:number;require_complete:boolean}
export interface Decision {verdict:'hold'|'eligible';passed:number;total:number;pass_rate:number;critical_failures:number;unresolved:number;reasons:string[];policy:ReleasePolicy}
export interface ModelEndpointDefinition {schema_version:'1.0';id:string;name:string;protocol:string;base_url:string;model:string;authentication:{type:'none'|'bearer';environment_variable?:string|null};generation:{temperature:number|null;max_output_tokens:number;timeout_seconds:number;json_schema?:boolean};capabilities:{tools:boolean|null;streaming:boolean|null}}
export interface Connection {definition:ModelEndpointDefinition;api_key?:string}
export interface RunBundle {schema_version:'1.0';id:string;created_at:string;mode:'replay'|'live';provenance:string;versions:Record<string,string>;endpoint:ModelEndpointDefinition|null;judge_endpoint:ModelEndpointDefinition|null;expected_results:number;judge_calibration:Record<string,unknown>[];results:CaseResult[];decision:Decision}
export interface Profile {id:string;title:string;description:string;bundle:RunBundle}
export interface Calibration {id:string;label:string;case_id:string;text:string;citations:string[];disposition:string;as_of:string|null;retrieved_passage_ids:string[];expected_pass:boolean;explanation:string;actual_pass:boolean;weak_pass:boolean;matches_reference:boolean;result:CaseResult}
export interface Replays {provenance:string;profiles:Profile[];calibration:Calibration[]}
export interface Distribution {schema_version:'1.0';version:string;downloads:{edition:'python'|'react';href:string}[];checksums?:string}
export interface LabData {corpus:Corpus;cases:Case[];replays:Replays;distribution:Distribution}

