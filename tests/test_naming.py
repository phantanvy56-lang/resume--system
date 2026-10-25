from pathlib import Path

from resume_system.naming import output_dir, output_stem


def test_stem_with_company():
    task = {"company": "示例公司", "job_title": "运营实习生"}
    assert output_stem(task) == "示例公司_运营实习生"


def test_stem_without_company():
    assert output_stem({"job_title": "运营/产品"}) == "运营-产品"


def test_output_dir_nests_company_and_job():
    task = {"company": "示例公司", "job_title": "运营实习生"}
    p = output_dir(task, Path("/tmp/out"))
    assert p == Path("/tmp/out/示例公司/运营实习生")
