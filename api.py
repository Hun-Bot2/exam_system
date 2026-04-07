"""OpenAI / Google Gemini 기반 문제 생성 래퍼."""

import json
import os
import time
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI_BACKEND = os.getenv("AI_BACKEND", "gemini").lower()  # "openai" or "gemini"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 공통 설정
MAX_TOKENS = 1500
TEMPERATURE = 0.7
MAX_RETRIES = 3
RATE_LIMIT_WAIT = 15  # Gemini 무료 티어: 분당 15회 → 4초 간격으로도 충분하지만 여유 확보

# OpenAI 설정
OPENAI_MODEL = "gpt-3.5-turbo"
OPENAI_RATE_LIMIT_WAIT = 30  # OpenAI 무료 티어: 분당 3회

# Gemini 설정 (무료 티어: gemini-2.5-flash-lite 권장)
GEMINI_MODEL = "gemini-2.5-flash-lite"

REQUIRED_FIELDS = ["id", "unit", "question", "options", "answer", "type", "difficulty", "tags"]

# 학교 유형별 기본 정보 (JSON 파일 형식과 일치)
SCHOOL_CONFIG = {
    "중학교": {
        "description": "중학교 정보 교과 수준의 기초 개념 및 프로그래밍 입문 내용",
        "id_prefix": "MS",
        "num_options": 4,
        "units": [
            # I. 컴퓨팅 시스템
            "I. 컴퓨팅 시스템 - 네트워크의 구성",
            "I. 컴퓨팅 시스템 - 사물 인터넷",
            # II. 데이터
            "II. 데이터 - 디지털 데이터 압축",
            "II. 데이터 - 디지털 데이터 암호화",
            "II. 데이터 - 빅데이터 개념과 분석",
            # III. 알고리즘과 프로그래밍
            "III. 알고리즘과 프로그래밍 - 문제 분해와 모델링",
            "III. 알고리즘과 프로그래밍 - 알고리즘",
            "III. 알고리즘과 프로그래밍 - 프로그래밍의 이해",
            "III. 알고리즘과 프로그래밍 - 제어 구조의 응용",
            "III. 알고리즘과 프로그래밍 - 함수와 라이브러리",
            "III. 알고리즘과 프로그래밍 - 객체지향 프로그래밍",
            "III. 알고리즘과 프로그래밍 - 창의 융합 프로그래밍",
            # IV. 인공지능
            "IV. 인공지능 - 인공지능과 지능 에이전트",
            "IV. 인공지능 - 기계학습의 개념",
            "IV. 인공지능 - 기계학습의 모델과 구현",
            # V. 디지털 문화
            "V. 디지털 문화 - 디지털 사회와 진로",
            "V. 디지털 문화 - 정보 보호와 보안",
        ],
    },
    "고등학교": {
        "description": "일반 고등학교 정보 교과 수준의 컴퓨팅 사고력 및 프로그래밍 내용",
        "id_prefix": "HS",
        "num_options": 4,
        "units": [
            # I. 컴퓨팅 시스템
            "I. 컴퓨팅 시스템 - 컴퓨팅 시스템의 구성과 동작",
            "I. 컴퓨팅 시스템 - 피지컬 컴퓨팅",
            # II. 데이터
            "II. 데이터 - 데이터의 표현과 관리",
            "II. 데이터 - 데이터의 구조화와 분석",
            # III. 알고리즘과 프로그래밍
            "III. 알고리즘과 프로그래밍 - 추상화와 알고리즘",
            "III. 알고리즘과 프로그래밍 - 프로그래밍",
            "III. 알고리즘과 프로그래밍 - 문제 해결과 프로그래밍",
            # IV. 인공지능
            "IV. 인공지능 - 인공지능과 데이터",
            "IV. 인공지능 - 인공지능과 문제 해결",
            # V. 디지털 문화
            "V. 디지털 문화 - 디지털 사회와 직업",
            "V. 디지털 문화 - 디지털 시민과 윤리",
        ],
    },
    "소프트웨어 고등학교": {
        "description": "소프트웨어 특성화 고등학교 전문 교육과정 (공통교과 + 인공지능소프트웨어과 전문교과)",
        "id_prefix": "SHS",
        "num_options": 5,
        "units": [
            # 공통교과 - 프로그래밍
            "프로그래밍 - 프로그래밍 기초",
            "프로그래밍 - 자료형과 변수",
            "프로그래밍 - 제어 구조",
            "프로그래밍 - 함수",
            "프로그래밍 - 객체지향 프로그래밍",
            # 공통교과 - 자료구조
            "자료구조 - 배열과 리스트",
            "자료구조 - 스택과 큐",
            "자료구조 - 트리",
            "자료구조 - 그래프",
            "자료구조 - 정렬과 탐색",
            # 공통교과 - 시스템프로그래밍
            "시스템프로그래밍 - 운영체제 기초",
            "시스템프로그래밍 - 프로세스와 메모리 관리",
            "시스템프로그래밍 - 파일 시스템",
            # 공통교과 - 네트워크프로그래밍
            "네트워크프로그래밍 - 네트워크 기초",
            "네트워크프로그래밍 - 소켓 프로그래밍",
            "네트워크프로그래밍 - 웹 프로그래밍",
            # 공통교과 - 응용프로그래밍개발
            "응용프로그래밍개발 - 소프트웨어 설계",
            "응용프로그래밍개발 - GUI 프로그래밍",
            "응용프로그래밍개발 - 프로젝트 개발",
            # 전문교과 (인공지능소프트웨어과) - 컴퓨터시스템일반
            "컴퓨터시스템일반 - 컴퓨터 구조",
            "컴퓨터시스템일반 - 자료 표현",
            "컴퓨터시스템일반 - 운영체제",
            # 전문교과 (인공지능소프트웨어과) - 데이터베이스프로그래밍
            "데이터베이스프로그래밍 - 데이터베이스 기초",
            "데이터베이스프로그래밍 - SQL",
            "데이터베이스프로그래밍 - 데이터베이스 설계",
            # 전문교과 (인공지능소프트웨어과) - 로봇지능개발
            "로봇지능개발 - 로봇 기초 및 센서",
            "로봇지능개발 - 인공지능 알고리즘",
            "로봇지능개발 - 로봇 프로그래밍",
        ],
    },
}


# ------------------------------------------------------------------
# 캐시 싱글턴 (Streamlit 프로세스 내 모든 세션이 공유)
# ------------------------------------------------------------------

@st.cache_resource
def _get_cache():
    from cache import QuestionCache
    return QuestionCache(redis_url=REDIS_URL)


# ------------------------------------------------------------------
# 프롬프트 빌더 / 파서
# ------------------------------------------------------------------

def _build_prompt(student_level: str, num_questions: int, school_type: str, unit: Optional[str]) -> str:
    """OpenAI / Gemini에 전달할 프롬프트 문자열 생성. JSON 파일 형식과 동일한 구조로 생성."""
    config = SCHOOL_CONFIG.get(school_type, SCHOOL_CONFIG["중학교"])
    id_prefix = config["id_prefix"]
    num_options = config["num_options"]
    description = config["description"]

    if unit:
        unit_text = unit
    else:
        unit_list = "\n".join(f"  - {u}" for u in config["units"])
        unit_text = f"아래 단원 중 하나를 선택하여 출제하세요:\n{unit_list}"

    answer_range = ", ".join(str(i) for i in range(1, num_options + 1))
    example_options = [f"{i}번 선택지" for i in range(1, num_options + 1)]

    return f"""
당신은 한국 {school_type} 정보 교과 문제를 출제하는 전문 교사입니다.
아래 조건에 맞는 객관식 문제를 정확히 {num_questions}개 생성해주세요.

[출제 조건]
- 학교 유형: {school_type} ({description})
- 난이도: {student_level} (하: 기초 개념, 중: 응용 이해, 상: 심화 분석)
- 단원: {unit_text}
- 문제 유형: 객관식 (선택지 {num_options}개)

[JSON 출력 형식]
반드시 아래 JSON 배열 형식으로만 응답하세요. 설명, 주석, 마크다운 코드블록 없이 순수 JSON만 출력하세요.

[
  {{
    "id": "{id_prefix}001",
    "unit": "단원명",
    "question": "문제 내용을 여기에 작성합니다.",
    "options": {json.dumps(example_options, ensure_ascii=False)},
    "answer": "정답 번호 ({answer_range} 중 하나의 숫자)",
    "type": "객관식",
    "difficulty": "{student_level}",
    "tags": ["관련태그1", "관련태그2"]
  }}
]

[출제 주의사항]
- 반드시 순수 JSON 배열만 출력할 것 (다른 텍스트 절대 포함 금지)
- 선택지는 반드시 {num_options}개로 구성할 것
- 정답은 {answer_range} 중 하나의 숫자(문자열)로만 표시할 것
- 각 문제는 교육과정에 부합하고 명확한 하나의 정답이 있어야 함
- 오답 선택지도 그럴듯하게 구성하여 변별력을 갖출 것
- difficulty 필드는 반드시 "{student_level}"로 표시할 것
- tags는 문제와 관련된 핵심 개념 키워드 1~3개로 구성할 것
""".strip()


def _parse_and_validate(content: str, school_type: str, num_questions: int) -> list:
    """API 응답 문자열을 파싱하고 필드 유효성 검증 후 정규화된 문제 목록 반환."""
    config = SCHOOL_CONFIG.get(school_type, SCHOOL_CONFIG["중학교"])
    num_options = config["num_options"]
    id_prefix = config["id_prefix"]

    # 마크다운 코드블록 제거 (```json ... ``` 형태 대응)
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    questions = json.loads(content)

    if not isinstance(questions, list):
        raise ValueError("응답이 JSON 배열 형식이 아닙니다.")

    valid_answers = list(range(1, num_options + 1))

    for idx, question in enumerate(questions):
        for field in REQUIRED_FIELDS:
            if field not in question:
                raise ValueError(f"문제 {idx + 1}에 필수 필드 '{field}'가 없습니다.")

        if not isinstance(question["options"], list) or len(question["options"]) != num_options:
            raise ValueError(
                f"문제 {idx + 1}의 선택지가 {num_options}개가 아닙니다. "
                f"(현재 {len(question.get('options', []))}개)"
            )

        if not str(question["answer"]).isdigit() or int(question["answer"]) not in valid_answers:
            raise ValueError(
                f"문제 {idx + 1}의 정답이 1~{num_options} 사이의 숫자가 아닙니다. "
                f"(현재 값: '{question['answer']}')"
            )

        # ID를 학교 유형에 맞는 형식으로 재할당
        question["id"] = f"{id_prefix}{idx + 1:03d}"
        # 정답을 항상 문자열로 정규화
        question["answer"] = str(question["answer"])
        # type 필드 강제 정규화
        question["type"] = "객관식"

    return questions


# ------------------------------------------------------------------
# 백엔드 API 호출 (스피너 없음 — 호출자가 래핑)
# ------------------------------------------------------------------

def _call_backend_api(prompt: str, school_type: str, num_questions: int) -> list:
    """AI_BACKEND에 따라 OpenAI 또는 Gemini를 호출. 스피너는 호출자가 관리."""
    if AI_BACKEND == "openai":
        if not OPENAI_API_KEY:
            st.error("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
            return []
        return _generate_via_openai(prompt, school_type, num_questions)
    else:
        if not GEMINI_API_KEY:
            st.error("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
            return []
        return _generate_via_gemini(prompt, school_type, num_questions)


def _generate_via_openai(prompt: str, school_type: str, num_questions: int) -> list:
    """OpenAI Chat Completions API 호출 (스피너 없음)."""
    import openai

    for attempt in range(MAX_RETRIES):
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            content = response.choices[0].message.content.strip()
            return _parse_and_validate(content, school_type, num_questions)

        except json.JSONDecodeError as exc:
            if attempt == MAX_RETRIES - 1:
                st.error("AI 응답이 올바른 JSON 형식이 아닙니다.")
                st.error(f"JSON 파싱 오류: {exc}")
            else:
                time.sleep(2 ** attempt)

        except openai.RateLimitError:
            if attempt == MAX_RETRIES - 1:
                st.error("OpenAI API 요청 한도를 초과했습니다. 무료 티어는 분당 3회로 제한됩니다.")
            else:
                wait = OPENAI_RATE_LIMIT_WAIT * (attempt + 1)
                st.warning(f"API 요청 한도 초과. {wait}초 후 재시도합니다... ({attempt + 1}/{MAX_RETRIES - 1})")
                time.sleep(wait)

        except Exception as exc:
            if attempt == MAX_RETRIES - 1:
                st.error(f"문제 생성 중 오류가 발생했습니다: {exc}")
            else:
                time.sleep(2 ** attempt)

    return []


def _generate_via_gemini(prompt: str, school_type: str, num_questions: int) -> list:
    """Google Gemini API 호출 (스피너 없음)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_TOKENS,
                ),
            )
            content = response.text.strip()
            return _parse_and_validate(content, school_type, num_questions)

        except json.JSONDecodeError as exc:
            if attempt == MAX_RETRIES - 1:
                st.error("AI 응답이 올바른 JSON 형식이 아닙니다.")
                st.error(f"JSON 파싱 오류: {exc}")
            else:
                time.sleep(2 ** attempt)

        except Exception as exc:
            err_str = str(exc)
            # Gemini 429 처리
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                if attempt == MAX_RETRIES - 1:
                    st.error("Gemini API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
                else:
                    wait = RATE_LIMIT_WAIT * (attempt + 1)
                    st.warning(f"API 요청 한도 초과. {wait}초 후 재시도합니다... ({attempt + 1}/{MAX_RETRIES - 1})")
                    time.sleep(wait)
            else:
                if attempt == MAX_RETRIES - 1:
                    st.error(f"문제 생성 중 오류가 발생했습니다: {exc}")
                else:
                    time.sleep(2 ** attempt)

    return []


# ------------------------------------------------------------------
# 풀 보충
# ------------------------------------------------------------------

def _replenish_pool(cache, difficulty: str, school_type: str, unit: Optional[str]) -> None:
    """풀이 POOL_MIN 미만일 때 POOL_REPLENISH개 문제를 생성해 풀에 추가."""
    from cache import POOL_REPLENISH
    prompt = _build_prompt(difficulty, POOL_REPLENISH, school_type, unit)
    cache.check_and_increment_rate_limit()
    cache.increment_api_calls()
    questions = _call_backend_api(prompt, school_type, POOL_REPLENISH)
    if questions:
        cache.push_to_pool(school_type, difficulty, unit, questions)


# ------------------------------------------------------------------
# 퍼블릭 API — 3계층 폭포
# ------------------------------------------------------------------

def generate_questions_via_api(
    student_level: str,
    num_questions: int,
    school_type: str,
    unit: Optional[str] = None,
) -> list:
    """캐시 워터폴(풀 → 코얼레싱 → 직접 API)을 통해 문제를 반환."""
    cache = _get_cache()

    if cache.is_available():
        # ── Path A: 풀 히트 ──────────────────────────────────────────
        questions = cache.serve_from_pool(school_type, student_level, unit, num_questions)
        if questions:
            cache.increment_cache_hits()
            cache.increment_total_served(len(questions))
            # 풀이 낮아졌으면 보충
            if cache.needs_replenishment(school_type, student_level, unit):
                with st.spinner("문제 풀 보충 중..."):
                    _replenish_pool(cache, student_level, school_type, unit)
            return questions

        # ── Path B: 캐시 미스 → 코얼레싱 ────────────────────────────
        prompt = _build_prompt(student_level, num_questions, school_type, unit)
        prompt_hash = cache._prompt_hash(school_type, student_level, unit, num_questions)

        if cache.try_acquire_leader(prompt_hash):
            # 리더: 직접 API 호출 후 결과 publish
            with st.spinner("AI가 문제를 생성하고 있습니다... 잠시만 기다려주세요."):
                cache.check_and_increment_rate_limit()
                cache.increment_api_calls()
                result = _call_backend_api(prompt, school_type, num_questions)

            if result:
                cache.push_to_pool(school_type, student_level, unit, result)
                cache.publish_result(prompt_hash, result)
                cache.increment_total_served(len(result))
                return result
            else:
                cache.publish_failure(prompt_hash)
                return []
        else:
            # 팔로워: 리더 결과를 BLPOP으로 대기
            with st.spinner("다른 사용자의 생성 완료 대기 중... 잠시만 기다려주세요."):
                result = cache.wait_for_result(prompt_hash)

            if result:
                cache.increment_cache_hits()
                cache.increment_total_served(len(result))
                return result
            else:
                # 타임아웃 또는 리더 실패 → 직접 호출 폴백
                st.warning("대기 시간이 초과되었습니다. 직접 생성합니다.")
                with st.spinner("AI가 문제를 생성하고 있습니다... 잠시만 기다려주세요."):
                    cache.check_and_increment_rate_limit()
                    cache.increment_api_calls()
                    fallback = _call_backend_api(prompt, school_type, num_questions)
                if fallback:
                    cache.increment_total_served(len(fallback))
                return fallback

    else:
        # ── Path C: Redis 없음 — 원본 동작 ──────────────────────────
        prompt = _build_prompt(student_level, num_questions, school_type, unit)
        with st.spinner("AI가 문제를 생성하고 있습니다... 잠시만 기다려주세요."):
            return _call_backend_api(prompt, school_type, num_questions)
