# Intent enum 정의 — 새 intent 추가 시 이 파일에 값을 추가하고 router.py에 매핑 등록
from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    INTENT_A = "INTENT_A"
    INTENT_B = "INTENT_B"
    UNKNOWN = "UNKNOWN"
