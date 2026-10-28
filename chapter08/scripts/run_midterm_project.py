"""chapter08 폴더에서 python scripts/run_midterm_project.py로 전체 과정을 실행한다.

공식 분석 함수는 수정하지 않았다. 입력 체크섬과 실행 경로만 고정한다.
"""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.prepare_inputs import prepare_inputs
from src.midterm_project import run_midterm_project


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    prepare_inputs(ROOT)
    out = args.output_root.resolve()
    result = run_midterm_project(
        raw_dir=ROOT / "data/raw",
        processed_dir=out / "data/processed",
        report_dir=out / "reports",
        figure_dir=out / "reports/figures",
        show_figures=False,
    )
    print("[최종 Validation]")
    print(result["project_validation"].to_string(index=False))
    print("[총합 검증]")
    print(result["analysis_tables"]["total_consistency_check"].to_string(index=False))
    outputs = result["saved_tables"] + result["saved_figures"] + [result["report_path"]]
    assert len(outputs) == 19 and all(p.is_file() and p.stat().st_size for p in outputs)
    prepare_inputs(ROOT)
    print("공식 산출물 19개 생성 / 입력·코드 체크섬 유지 / 전체 재실행 PASS")


if __name__ == "__main__":
    main()
