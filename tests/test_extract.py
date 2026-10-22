import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from extract import clean_text, extract_skills  # noqa: E402


def test_basic_skills():
    text = clean_text({"title": "Data Engineer", "description": "<p>Python, SQL and Airflow on AWS</p>"})
    assert {"python", "sql", "airflow", "aws"} <= extract_skills(text)


def test_javascript_is_not_java():
    skills = extract_skills(clean_text({"description": "We use JavaScript and React"}))
    assert "javascript" in skills and "java" not in skills


def test_tags_are_used():
    skills = extract_skills(clean_text({"title": "Dev", "tags": ["docker", "kubernetes"]}))
    assert {"docker", "kubernetes"} <= skills


def test_go_not_matched_in_plain_text():
    assert "go" not in extract_skills(clean_text({"description": "ready to go and grow"}))


def test_remoteok_tags_are_ignored():
    payload = {"position": "Account Manager", "tags": ["golang", "python"]}
    assert extract_skills(clean_text(payload, "remoteok")) == set()
    assert "python" in extract_skills(clean_text(payload, "arbeitnow"))
