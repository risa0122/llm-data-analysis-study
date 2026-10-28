"""공식 원본의 고정 버전을 받는다. 기존 파일이 다르면 덮어쓰지 않고 중단한다."""
from pathlib import Path
from urllib.request import urlopen
import hashlib
import json


ROOT = Path(__file__).resolve().parents[1]


def prepare_inputs(root=ROOT):
    root = Path(root)
    manifest = json.loads((root / "input_manifest.json").read_text(encoding="utf-8"))
    source = f"https://raw.githubusercontent.com/{manifest['repository']}/{manifest['commit']}"
    rows = []
    for relative, expected in manifest["sha256"].items():
        path = root / relative
        if not path.exists():
            if not relative.startswith("data/raw/"):
                raise FileNotFoundError(f"필요 코드가 없습니다: {relative}")
            with urlopen(f"{source}/{relative}", timeout=30) as response:
                content = response.read()
            if hashlib.sha256(content).hexdigest() != expected:
                raise ValueError(f"다운로드 체크섬 불일치: {relative}")
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as output:
                output.write(content)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"기존 파일 체크섬 불일치(덮어쓰지 않음): {relative}")
        rows.append({"file": relative, "sha256": actual, "status": "PASS"})
    return rows


if __name__ == "__main__":
    for result in prepare_inputs():
        print(result["file"], result["status"])
