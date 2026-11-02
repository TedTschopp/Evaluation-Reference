import sys
import pytest
from eval_lab.cli import main

def test_serve_from_wrong_folder_explains_how_to_start(monkeypatch,tmp_path,capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys,"argv",["eval-lab","serve"])
    with pytest.raises(SystemExit) as error:main()
    assert error.value.code==2
    message=capsys.readouterr().err
    assert "built React site is missing" in message
    assert "Python edition" in message and "Streamlit" in message

def test_validate_reports_the_bundled_teaching_results(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["eval-lab","validate"])
    main()
    output=capsys.readouterr().out
    assert "31 documents" in output and "320 passages" in output
    assert "8/12, hold" in output and "11/12, hold" in output and "12/12, eligible" in output

def test_rebuild_refreshes_downloaded_browser_data_with_actual_evaluator(monkeypatch,tmp_path,capsys):
    import json
    from eval_lab import replay
    source=tmp_path/"data";source.mkdir()
    built=tmp_path/"web/dist/data";built.mkdir(parents=True)
    (built/"corpus.json").write_text("{}")
    monkeypatch.setattr(replay,"DATA_DIR",source)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys,"argv",["eval-lab","rebuild-replays"])
    main()
    stored=json.loads((source/"replays.json").read_text())
    browser=json.loads((built/"replays.json").read_text())
    assert stored==browser
    assert [p["bundle"]["decision"]["passed"] for p in browser["profiles"]]==[8,11,12]
    assert "Calibration: 8/8" in capsys.readouterr().out
