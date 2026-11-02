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

