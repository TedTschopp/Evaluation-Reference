"""Independent Python teaching webapp. Start with: streamlit run python_app/app.py"""
from __future__ import annotations
import asyncio
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"python_app"))
import pandas as pd
import streamlit as st
from eval_lab.corpus import Corpus,load_json,case_by_id
from eval_lab.models import EndpointConnection,ModelEndpointDefinition,ReleasePolicy,RunBundle,RunRequest,decide_release
from eval_lab.providers import safe_error,test_connection
from eval_lab.validation import validate_imported_bundle
from jobs import start_job

st.set_page_config(page_title="Did it answer the question? · Python lab",page_icon="📜",layout="wide")
st.markdown("""<style>
:root{--primary-color:#00446f} .block-container{padding-top:2.5rem;max-width:1400px}
h1,h2,h3{letter-spacing:-.035em}div[data-testid=stMetric]{background:#00446f0d;border:1px solid #64748b33;padding:1rem;border-radius:.35rem}
[data-testid=stSidebar]{border-right:1px solid #64748b33}.stCaption{line-height:1.7}
</style>""",unsafe_allow_html=True)

@st.cache_data
def assets():
    return load_json("corpus.json"),load_json("cases.json"),load_json("replays.json")
corpus_data,case_data,replays=assets()
corpus=Corpus(corpus_data)
all_cases=case_data["cases"]
labels=["1 · Define the job","2 · Follow the evidence","3 · Change the boundary","4 · Test the grader","5 · Compare versions","6 · Decide what can ship"]
with st.sidebar:
    st.caption("TEDT.ORG / PUBLIC WORKBENCH")
    st.header("AI evaluation lab")
    lesson=st.radio("Guided walkthrough",labels,label_visibility="collapsed")
    mode=st.radio("Execution mode",["Replay","Live"],horizontal=True)
    profile=st.selectbox("Agent version",[p["id"] for p in replays["profiles"]],
        index=1,format_func=lambda x:next(p["title"] for p in replays["profiles"] if p["id"]==x))
    st.caption("Microsoft Agent Framework 1.24.0\n\n31 texts · 12 cases · about 20 minutes")
    st.link_button("Read Ted's article","https://tedt.org/Your-AI-Passed-the-Test/")
    imported=st.file_uploader("Import a RunBundle",type=["json"],max_upload_size=16)
    if imported:
        try:
            value=validate_imported_bundle(imported.getvalue())
            unknown={r.case_id for r in value.results}-{c["id"] for c in all_cases}
            if unknown or len(value.results)>36 or value.expected_results<len(value.results):
                raise ValueError("This bundle does not match the twelve-case reference.")
            st.session_state["imported_bundle"]=value
            st.caption("Imported data is displayed, not re-executed.")
        except Exception:
            st.error("This file does not match the RunBundle 1.0 contract.")
    if st.button("Return to bundled examples"):
        st.session_state.pop("imported_bundle",None)
        st.session_state.pop("live_bundle",None)
        st.rerun()

st.caption("AN AZURE-INDEPENDENT REFERENCE · PYTHON EDITION")
st.title("Did it answer the question?")
st.write("A correct fact can still be the wrong answer. Follow the evidence, test the grader, and connect the results to a release decision.")
m1,m2,m3=st.columns(3)
m1.metric("Source texts",31);m2.metric("Test cases",12);m3.metric("Default critical failures allowed",0)
st.divider()
step=labels.index(lesson)
titles=["The number is real. The answer is wrong.","An authentic source can be the wrong source.",
        "Remove the evidence. Then restore it.","The grader needs a test, too.",
        "Compare the same work.","Make the requirement part of the release decision."]
st.header(titles[step])
subset_ids=[
    ["ratified-1791","proposed-1789"],
    ["senate-1789","senate-1914","prohibition-1925","prohibition-1935","tax-articles","tax-constitution"],
    ["evidence-restricted","evidence-restored","ambiguity","clear-context"],
][step] if step<3 else [c["id"] for c in all_cases]
case_id=st.selectbox("Test case",subset_ids,format_func=lambda x:case_by_id(x)["title"])
case=case_by_id(case_id)

def connection_form(prefix,title):
    st.subheader(title)
    left,right=st.columns(2)
    protocol=left.selectbox("API format",["openai_chat_completions","ollama"],key=prefix+"protocol")
    model=right.text_input("Model identifier",key=prefix+"model",placeholder="Your model name")
    url=st.text_input("Base URL",value="https://api.openai.com/v1",key=prefix+"url",
        help="For native Ollama use its server root, e.g. http://localhost:11434, without /v1.")
    auth=st.selectbox("Authentication",["none","bearer"],index=0 if protocol=="ollama" else 1,key=prefix+"auth")
    key=st.text_input("API key · this session only",type="password",key=prefix+"key") if auth=="bearer" else None
    with st.expander("Generation settings"):
        include_temperature=st.checkbox("Send temperature setting",True,key=prefix+"send-temp")
        temperature=st.number_input("Temperature",0.0,2.0,0.0,.1,key=prefix+"temp")
        tokens=st.number_input("Maximum output tokens",64,4096,1200,key=prefix+"tokens")
        timeout=st.number_input("Timeout in seconds",5,120,60,key=prefix+"timeout")
        json_schema=st.checkbox("Use structured JSON schema output",False,key=prefix+"json")
    definition=ModelEndpointDefinition(id=prefix.strip("-"),name=title,protocol=protocol,base_url=url,
        model=model or "not-configured",authentication={"type":auth},
        generation={"temperature":temperature if include_temperature else None,"max_output_tokens":tokens,"timeout_seconds":timeout,"json_schema":json_schema})
    return EndpointConnection(definition=definition,api_key=key),bool(model)

if mode=="Live":
    with st.expander("Configure and run a live model",expanded=True):
        st.caption("The agent uses only the documents authorized for each case. Model keys stay in this Streamlit session's memory.")
        agent_connection,configured=connection_form("agent-","Document agent")
        fingerprint=hashlib.sha256((agent_connection.definition.model_dump_json()+(agent_connection.api_key.get_secret_value() if agent_connection.api_key else "")).encode()).hexdigest()
        if st.button("Test connection and function calling",disabled=not configured):
            try:
                with st.spinner("Testing text generation and a harmless function call…"):
                    probe=asyncio.run(test_connection(agent_connection,hosted=False))
                st.session_state["probe"]=(fingerprint,probe)
            except Exception as error:
                st.error(safe_error(error))
        probe_state=st.session_state.get("probe")
        verified=bool(probe_state and probe_state[0]==fingerprint and probe_state[1]["tools"])
        if probe_state and probe_state[0]==fingerprint:
            st.info(probe_state[1]["message"])
        use_judge=st.checkbox("Add an independent AI judge")
        judge_connection=None
        if use_judge:
            judge_connection,_=connection_form("judge-","Independent AI judge")
            st.caption("Eight source-checked calibration responses are tested before the judge's verdicts are accepted.")
        selected=st.radio("Run scope",["Selected case","All twelve cases"],horizontal=True)
        repetitions=st.selectbox("Attempts per case",[1,3])
        running=bool(st.session_state.get("job") and not st.session_state["job"].done.is_set())
        if st.button("Run live evaluation",type="primary",disabled=not verified or running):
            try:
                request=RunRequest(case_ids=[case_id] if selected=="Selected case" else [c["id"] for c in all_cases],
                    profile=profile,agent=agent_connection,judge=judge_connection,repetitions=repetitions)
                st.session_state["job"]=start_job(request)
                st.session_state["job_log"]=[]
            except Exception as error:
                st.error(safe_error(error))
        st.download_button("Export endpoint definition (no key)",agent_connection.definition.model_dump_json(indent=2),
            "model-endpoint.json","application/json")

    @st.fragment(run_every="1s")
    def job_progress():
        job=st.session_state.get("job")
        if not job:
            return
        log=st.session_state.setdefault("job_log",[])
        while not job.events.empty():
            event=job.events.get_nowait()
            if event["type"] in {"case_started","case_completed","calibration","connection"}:
                log.append(event["type"]+" · "+event.get("case_id",str(event.get("data",{}).get("label",""))))
        if not job.done.is_set():
            st.info("Live evaluation is running. "+" · ".join(log[-2:]))
            if st.button("Stop current run"):
                job.cancel()
        elif not st.session_state.get("job_consumed") is job:
            st.session_state["job_consumed"]=job
            if job.bundle:
                st.session_state["live_bundle"]=job.bundle
            if job.error:
                st.session_state["job_error"]=job.error
            st.rerun()
    job_progress()
    if st.session_state.get("job_error"):
        st.error(st.session_state["job_error"])

selected_profile=next(p for p in replays["profiles"] if p["id"]==profile)
bundle=RunBundle.model_validate(selected_profile["bundle"])
if st.session_state.get("live_bundle") and mode=="Live":
    bundle=st.session_state["live_bundle"]
if st.session_state.get("imported_bundle"):
    bundle=st.session_state["imported_bundle"]
st.caption(("Captured live run" if bundle.mode=="live" else "Replay · authored teaching responses")+" · scores produced by real Microsoft LocalEvaluator")
result=next((r for r in reversed(bundle.results) if r.case_id==case_id),None)

if step<3:
    st.info(case["question"])
    with st.expander("What successful work requires"):
        st.write(case["expected_behavior"])
        st.caption("Authorized documents: "+", ".join(case["allowed_document_ids"]))
    if result:
        st.subheader("Agent response")
        st.write(result.answer.text)
        st.caption("Disposition: "+result.answer.disposition+" · Scope: "+str(result.answer.as_of))
        if result.error: st.error(result.error)
        left,right=st.columns(2)
        weak=next((g for g in result.grades if g.kind=="weak_checker"),None)
        left.metric("Weak checker",weak.status if weak else "Not assessed")
        right.metric("Task-aware evaluation",result.status)
        st.dataframe(pd.DataFrame([{"Criterion":g.label,"Status":g.status,"Required":g.required,"Explanation":g.reason} for g in result.grades]),hide_index=True,width="stretch")
        with st.expander("Observable action trace"):
            for event in result.events:
                st.markdown("**"+event.get("name",event["type"])+"**")
                if event.get("arguments"):st.json(event["arguments"])
                if event.get("passage_ids"):st.write(", ".join(event["passage_ids"]))
        with st.expander("Inspect the actual SDK output"):
            st.json(result.framework)
    else:
        st.info("This run contains no result for the selected case.")
elif step==3:
    if bundle.judge_calibration:
        st.subheader("This run's AI judge calibration")
        st.dataframe(pd.DataFrame(bundle.judge_calibration),hide_index=True,width="stretch")
        st.caption("A mismatch or error leaves this judge's required assessments unresolved.")
    rows=replays["calibration"]
    st.caption("Eight authored responses with source-checked reference labels. This small set illustrates calibration, not general grader accuracy.")
    st.dataframe(pd.DataFrame([{"Response":r["label"],"Reference":r["expected_pass"],"Weak":r["weak_pass"],
        "Task-aware":r["actual_pass"],"Matches reference":r["matches_reference"]} for r in rows]),hide_index=True,width="stretch")
    cid=st.selectbox("Inspect calibration",[r["id"] for r in rows],format_func=lambda x:next(r["label"] for r in rows if r["id"]==x))
    row=next(r for r in rows if r["id"]==cid)
    st.write(row["text"]);st.info(row["explanation"])
    result=row["result"]
    st.json(row["result"]["grades"])
elif step==4:
    frame=pd.DataFrame([{"Version":p["title"],"Passed cases":p["bundle"]["decision"]["passed"]} for p in replays["profiles"]])
    st.bar_chart(frame,x="Version",y="Passed cases",horizontal=True)
    st.dataframe(pd.DataFrame([{"Case":c["title"],**{p["id"]:next(r["status"] for r in p["bundle"]["results"] if r["case_id"]==c["id"]) for p in replays["profiles"]}} for c in all_cases]),hide_index=True,width="stretch")
    st.info("The candidate improves from 8/12 to 11/12, but its critical ratification error still blocks release.")
else:
    a,b=st.columns(2)
    initial=bundle.decision.policy
    threshold=a.slider("Minimum case pass rate",0,100,round(initial.minimum_pass_rate*100),1,key=bundle.id+"threshold")
    critical=b.selectbox("Critical failures allowed",sorted({0,1,initial.maximum_critical_failures}),index=sorted({0,1,initial.maximum_critical_failures}).index(initial.maximum_critical_failures),key=bundle.id+"critical")
    complete=st.checkbox("Require the complete suite",initial.require_complete,key=bundle.id+"complete")
    policy=ReleasePolicy(id="teaching-default-v1" if (threshold,critical,complete)==(90,0,True) else "interactive-policy",
        minimum_pass_rate=threshold/100,maximum_critical_failures=critical,require_complete=complete)
    decision=decide_release(bundle.results,policy,bundle.expected_results)
    bundle=bundle.model_copy(update={"decision":decision})
    st.subheader("Hold this version." if decision.verdict=="hold" else "Meets the selected policy.")
    st.write(f"{decision.passed}/{decision.total} passes · {decision.critical_failures} critical failures · {decision.unresolved} unresolved")
    for reason in decision.reasons:st.write("• "+reason)
    if policy.id!="teaching-default-v1":st.warning("The policy changed; the underlying agent responses and grades did not.")
    st.info("Evaluation does not repair the agent. Investigate the failure, make a deliberate change, then rerun the cases and successful controls.")

st.divider()
with st.expander("Evidence desk and complete corpus",expanded=step<3):
    retrieved=[]
    if result:
        events=result.events if hasattr(result,"events") else result.get("events",[])
        retrieved=list(dict.fromkeys(pid for event in events for pid in event.get("passage_ids",[])))
    tabs=st.tabs(["Retrieved evidence","All 31 texts"])
    with tabs[0]:
        if retrieved:
            pid=st.selectbox("Passage returned by a tool",retrieved)
            p=corpus.passages[pid];d=corpus.documents[p["document_id"]]
            st.subheader(p["label"]);st.write(p["text"]);st.code(pid)
            with st.expander("Archival annotations (separate from primary text)"):
                for note in d["annotations"]:st.write(note)
            st.link_button("National Archives source",d["source_url"])
        else:
            st.caption("This response has no retrieved factual passage to display.")
    with tabs[1]:
        did=st.selectbox("Document",list(corpus.documents),format_func=lambda x:corpus.documents[x]["title"])
        d=corpus.documents[did]
        st.subheader(d["title"]);st.caption(d["date"]+" · "+d["sha256"])
        st.text(d["text"]);st.link_button("Open source",d["source_url"])
st.download_button("Export RunBundle JSON",bundle.model_dump_json(indent=2),"evaluation-run.json","application/json")
st.caption("Source snapshots, annotations, and amendment relationships are bundled. Passing these cases is bounded evidence, not a production certification.")

