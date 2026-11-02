from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_python_walkthrough_all_lessons():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"python_app"/"app.py")).run(timeout=30)
    assert not app.exception
    assert app.title[0].value=="Did it answer the question?"
    for label in ["2 · Follow the evidence","3 · Change the boundary","4 · Test the grader","5 · Compare versions","6 · Decide what can ship"]:
        app.sidebar.radio[0].set_value(label).run(timeout=30)
        assert not app.exception,label
    app.sidebar.radio[1].set_value("Live").run(timeout=30)
    assert not app.exception

def test_local_preset_protocol_changes_and_invalid_url_do_not_crash():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"python_app"/"app.py")).run(timeout=30)
    app.sidebar.radio[1].set_value("Live").run(timeout=30)
    assert app.text_input(key="agent-url").value=="http://localhost:11434"
    assert app.text_input(key="agent-model").value=="llama3.2:3b"
    assert app.selectbox(key="agent-auth").value=="none"
    app.selectbox(key="agent-protocol").set_value("openai_chat_completions").run()
    assert app.text_input(key="agent-url").value=="https://api.openai.com/v1"
    assert app.selectbox(key="agent-auth").value=="bearer"
    app.selectbox(key="agent-protocol").set_value("ollama").run()
    assert app.text_input(key="agent-url").value=="http://localhost:11434"
    assert app.selectbox(key="agent-auth").value=="none"
    app.text_input(key="agent-url").set_value("http").run()
    assert not app.exception
    assert any("complete HTTP" in item.value for item in app.info)
    assert next(b for b in app.button if b.label=="Test connection and function calling").disabled

def test_return_to_examples_clears_imported_state_and_live_mode():
    from eval_lab.models import RunBundle
    from eval_lab.corpus import load_json
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"python_app"/"app.py")).run(timeout=30)
    app.sidebar.radio[1].set_value("Live").run()
    app.session_state["imported_bundle"]=RunBundle.model_validate(load_json("replays.json")["profiles"][2]["bundle"])
    app.session_state["job_error"]="An earlier connection failed."
    app.run()
    next(b for b in app.button if b.label=="Return to bundled examples").click().run()
    assert not app.exception
    assert app.sidebar.radio[1].value=="Replay"
    assert "imported_bundle" not in app.session_state
    assert "job_error" not in app.session_state

def test_lesson_buttons_work_without_the_sidebar():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"python_app"/"app.py")).run(timeout=30)
    for index in range(1,6):
        next(button for button in app.button if button.label.startswith("Next: ")).click().run()
        assert not app.exception
        assert app.sidebar.radio[0].value.startswith(str(index+1)+" · ")
    next(button for button in app.button if button.label=="Previous lesson").click().run()
    assert app.sidebar.radio[0].value.startswith("5 · ")

