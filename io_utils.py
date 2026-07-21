"""io_utils.py — 안전한 파일 저장 유틸

JSON 상태 파일을 원자적으로 저장한다. 기존 코드는 open(path,"w") + json.dump 를
직접 호출해서, 저장 도중 크래시/정전이 나면 파일이 잘리고(부분 기록) 로더가
`except: return {}` 로 조용히 빈 상태를 반환 → 다음 실행이 처음부터 다시 만들어
수개월치 이력이 사라질 수 있었다.

atomic_write_json 은 임시파일에 완전히 쓴 뒤 os.replace 로 교체하므로, 어느 순간에
크래시가 나도 원본은 항상 '직전의 온전한 상태'로 남는다. keep_bak=True 면 교체 직전
현재 파일을 .bak 로 1개 백업한다.
"""

import os
import json
import shutil
import tempfile


def atomic_write_json(path, obj, keep_bak=True, **json_kwargs):
    """obj 를 path 에 원자적으로 JSON 저장.

    json_kwargs 는 json.dump 에 그대로 전달(indent, default=float 등).
    ensure_ascii 는 지정 안 하면 False(한글 보존)로 기본 설정.
    """
    path = str(path)
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    json_kwargs.setdefault("ensure_ascii", False)

    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, **json_kwargs)
            f.flush()
            os.fsync(f.fileno())
        # 교체 직전, 파싱 가능한 마지막 상태를 .bak 로 보존
        if keep_bak and os.path.exists(path):
            try:
                shutil.copy2(path, path + ".bak")
            except Exception:
                pass
        os.replace(tmp, path)  # 원자적 교체 (같은 디렉터리 → 같은 파일시스템)
        tmp = None
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
