"""Redis 기반 3계층 캐시: 풀(pool) → 코얼레싱(coalescing) → API."""

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Optional

# Redis import — 없으면 graceful degradation
try:
    import redis as redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

# 학교 유형 → Redis 키에 사용할 ASCII 슬러그
SCHOOL_SLUG = {
    "중학교": "middle",
    "고등학교": "high",
    "소프트웨어 고등학교": "sw_high",
}

POOL_MIN = 10          # 이 미만이면 보충 필요
POOL_REPLENISH = 20    # 보충 시 생성할 문제 수
FANOUT_COPIES = 30     # publish_result가 밀어 넣을 복사본 수
COALESCE_TTL = 90      # inflight 락 TTL (초)
RESULT_TTL = 120       # result fan-out 채널 TTL (초)
POOL_TTL = 7 * 24 * 3600   # 풀 키 TTL (7일)
STATS_TTL = 32 * 24 * 3600  # 통계 키 TTL (32일)
RATE_LIMIT_MINUTE = 14  # 분당 허용 호출 수 (15 RPM 한도에서 1 버퍼)

# Lua: 원자적 팝 (LLEN 확인 → LRANGE → LTRIM)
_LUA_ATOMIC_POP = """
local count = tonumber(ARGV[1])
if redis.call('LLEN', KEYS[1]) < count then return nil end
local items = redis.call('LRANGE', KEYS[1], 0, count - 1)
redis.call('LTRIM', KEYS[1], count, -1)
return items
"""


class QuestionCache:
    """Redis 기반 문제 캐시 (풀 / 코얼레싱 / 레이트 리미터 / 통계)."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._available = False
        self._r: Optional[object] = None
        self._atomic_pop = None
        if _REDIS_AVAILABLE:
            self._connect(redis_url)

    # ------------------------------------------------------------------
    # 연결
    # ------------------------------------------------------------------

    def _connect(self, redis_url: str) -> None:
        try:
            r = redis_lib.from_url(
                redis_url,
                socket_connect_timeout=2,
                socket_timeout=5,
                decode_responses=True,
            )
            r.ping()
            self._r = r
            self._atomic_pop = r.register_script(_LUA_ATOMIC_POP)
            self._available = True
        except Exception:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    @staticmethod
    def _pool_key(school_type: str, difficulty: str, unit: Optional[str]) -> str:
        slug = SCHOOL_SLUG.get(school_type, school_type.replace(" ", "_"))
        unit_part = unit.replace(" ", "_") if unit else "nounit"
        # 한글 포함 가능하지만 짧게 해시
        unit_hash = hashlib.sha256(unit_part.encode()).hexdigest()[:8]
        return f"pool:{slug}:{difficulty}:{unit_hash}"

    @staticmethod
    def _prompt_hash(school_type: str, difficulty: str, unit: Optional[str], num_questions: int) -> str:
        raw = f"{school_type}|{difficulty}|{unit or ''}|{num_questions}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def _minute_key() -> str:
        return datetime.now(tz=timezone.utc).strftime("rl:gemini:minute:%Y%m%d%H%M")

    @staticmethod
    def _daily_key() -> str:
        return datetime.now(tz=timezone.utc).strftime("rl:gemini:daily:%Y%m%d")

    @staticmethod
    def _stat_key(name: str, date_str: Optional[str] = None) -> str:
        ds = date_str or datetime.now(tz=timezone.utc).strftime("%Y%m%d")
        return f"stats:{name}:{ds}"

    # ------------------------------------------------------------------
    # 풀 (pool)
    # ------------------------------------------------------------------

    def pool_size(self, school_type: str, difficulty: str, unit: Optional[str]) -> int:
        if not self._available:
            return 0
        try:
            return self._r.llen(self._pool_key(school_type, difficulty, unit))
        except Exception:
            return 0

    def serve_from_pool(self, school_type: str, difficulty: str, unit: Optional[str], count: int) -> Optional[list]:
        """풀에서 count개 문제를 원자적으로 팝. 부족하면 None."""
        if not self._available:
            return None
        try:
            key = self._pool_key(school_type, difficulty, unit)
            raw = self._atomic_pop(keys=[key], args=[count])
            if raw is None:
                return None
            return [json.loads(item) for item in raw]
        except Exception:
            return None

    def push_to_pool(self, school_type: str, difficulty: str, unit: Optional[str], questions: list) -> None:
        """문제 목록을 풀에 추가 (오른쪽에 push, 팝은 왼쪽)."""
        if not self._available or not questions:
            return
        try:
            key = self._pool_key(school_type, difficulty, unit)
            serialized = [json.dumps(q, ensure_ascii=False) for q in questions]
            self._r.rpush(key, *serialized)
            self._r.expire(key, POOL_TTL)
        except Exception:
            pass

    def needs_replenishment(self, school_type: str, difficulty: str, unit: Optional[str]) -> bool:
        return self.pool_size(school_type, difficulty, unit) < POOL_MIN

    # ------------------------------------------------------------------
    # 코얼레싱 (leader / follower)
    # ------------------------------------------------------------------

    def try_acquire_leader(self, prompt_hash: str) -> bool:
        """SET NX EX 90 으로 리더 락 획득 시도. 성공 시 True."""
        if not self._available:
            return True  # Redis 없으면 모두 리더처럼 직접 호출
        try:
            result = self._r.set(f"inflight:{prompt_hash}", "1", nx=True, ex=COALESCE_TTL)
            return result is True
        except Exception:
            return True

    def publish_result(self, prompt_hash: str, questions: list) -> None:
        """FANOUT_COPIES개의 복사본을 result 채널에 push, 락 해제."""
        if not self._available:
            return
        try:
            key = f"result:{prompt_hash}"
            serialized = json.dumps(questions, ensure_ascii=False)
            pipe = self._r.pipeline()
            for _ in range(FANOUT_COPIES):
                pipe.rpush(key, serialized)
            pipe.expire(key, RESULT_TTL)
            pipe.delete(f"inflight:{prompt_hash}")
            pipe.execute()
        except Exception:
            pass

    def publish_failure(self, prompt_hash: str) -> None:
        """실패 sentinel을 result 채널에 push, 락 해제."""
        if not self._available:
            return
        try:
            key = f"result:{prompt_hash}"
            pipe = self._r.pipeline()
            for _ in range(FANOUT_COPIES):
                pipe.rpush(key, "__FAILED__")
            pipe.expire(key, RESULT_TTL)
            pipe.delete(f"inflight:{prompt_hash}")
            pipe.execute()
        except Exception:
            pass

    def wait_for_result(self, prompt_hash: str) -> Optional[list]:
        """BLPOP으로 결과 대기 (최대 90초). __FAILED__ 또는 타임아웃이면 None."""
        if not self._available:
            return None
        try:
            key = f"result:{prompt_hash}"
            result = self._r.blpop(key, timeout=COALESCE_TTL)
            if result is None:
                return None
            _, value = result
            if value == "__FAILED__":
                return None
            return json.loads(value)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # 레이트 리미터
    # ------------------------------------------------------------------

    def check_and_increment_rate_limit(self) -> None:
        """분당 RATE_LIMIT_MINUTE 호출 한도 체크. 초과 시 다음 분까지 sleep."""
        if not self._available:
            return
        try:
            minute_key = self._minute_key()
            count = self._r.incr(minute_key)
            if count == 1:
                self._r.expire(minute_key, 65)  # 1분 + 5초 여유
            if count >= RATE_LIMIT_MINUTE:
                # 현재 분의 남은 시간 계산
                now = datetime.now(tz=timezone.utc)
                seconds_left = 60 - now.second + 1
                time.sleep(seconds_left)
        except Exception:
            pass

    def get_rate_limit_status(self) -> dict:
        """현재 분 호출 수, 다음 리셋까지 초, 오늘 누적 반환."""
        if not self._available:
            return {"current_minute": 0, "seconds_to_reset": 0, "daily_total": 0}
        try:
            minute_key = self._minute_key()
            daily_key = self._daily_key()
            now = datetime.now(tz=timezone.utc)
            current_minute = int(self._r.get(minute_key) or 0)
            daily_total = int(self._r.get(daily_key) or 0)
            seconds_to_reset = 60 - now.second
            return {
                "current_minute": current_minute,
                "seconds_to_reset": seconds_to_reset,
                "daily_total": daily_total,
            }
        except Exception:
            return {"current_minute": 0, "seconds_to_reset": 0, "daily_total": 0}

    # ------------------------------------------------------------------
    # 통계
    # ------------------------------------------------------------------

    def increment_api_calls(self) -> None:
        if not self._available:
            return
        try:
            key = self._stat_key("api_calls")
            self._r.incr(key)
            self._r.expire(key, STATS_TTL)
            # 일별 레이트 리밋 카운터도 증가
            daily_key = self._daily_key()
            self._r.incr(daily_key)
            self._r.expire(daily_key, 25 * 3600)
        except Exception:
            pass

    def increment_cache_hits(self) -> None:
        if not self._available:
            return
        try:
            key = self._stat_key("cache_hits")
            self._r.incr(key)
            self._r.expire(key, STATS_TTL)
        except Exception:
            pass

    def increment_total_served(self, count: int) -> None:
        if not self._available:
            return
        try:
            key = self._stat_key("total_served")
            self._r.incrby(key, count)
            self._r.expire(key, STATS_TTL)
        except Exception:
            pass

    def get_daily_stats(self, date_str: Optional[str] = None) -> dict:
        """특정 날짜(기본: 오늘)의 통계 반환."""
        if not self._available:
            return {"api_calls": 0, "cache_hits": 0, "total_served": 0, "hit_rate": 0.0}
        try:
            api_calls = int(self._r.get(self._stat_key("api_calls", date_str)) or 0)
            cache_hits = int(self._r.get(self._stat_key("cache_hits", date_str)) or 0)
            total_served = int(self._r.get(self._stat_key("total_served", date_str)) or 0)
            hit_rate = (cache_hits / total_served * 100) if total_served > 0 else 0.0
            return {
                "api_calls": api_calls,
                "cache_hits": cache_hits,
                "total_served": total_served,
                "hit_rate": round(hit_rate, 1),
            }
        except Exception:
            return {"api_calls": 0, "cache_hits": 0, "total_served": 0, "hit_rate": 0.0}

    def get_weekly_stats(self) -> list:
        """최근 7일 통계 (최신 날짜 먼저)."""
        from datetime import timedelta
        result = []
        today = datetime.now(tz=timezone.utc).date()
        for delta in range(7):
            d = today - timedelta(days=delta)
            ds = d.strftime("%Y%m%d")
            stats = self.get_daily_stats(ds)
            stats["date"] = d.strftime("%Y-%m-%d")
            result.append(stats)
        return result

    def get_all_pool_sizes(self) -> dict:
        """모든 학교 유형 × 난이도 풀 크기 반환. {school_type: {difficulty: count}}"""
        from api import SCHOOL_CONFIG  # 순환 방지를 위해 지연 import
        difficulties = ["하", "중", "상"]
        result = {}
        for school_type in SCHOOL_CONFIG:
            result[school_type] = {}
            for diff in difficulties:
                result[school_type][diff] = self.pool_size(school_type, diff, None)
        return result
