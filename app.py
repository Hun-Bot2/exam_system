"""Streamlit 기반 학생용 적응형 시험 응시 인터페이스."""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

# ── 페이지 설정 (반드시 첫 번째 st.* 호출) ──────────────────────────────────
st.set_page_config(
    page_title="정보교과 AI 시험",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from styles import inject_css, hero, section, badge, step_indicator, difficulty_badge
inject_css()

from api import generate_questions_via_api
from gnn_model import DifficultyPredictor

# ── 상수 ──────────────────────────────────────────────────────────────────────
APP_TITLE = "정보교과 AI 시험 시스템"
STEP_FLOW  = ["login", "setup", "generate", "solve", "feedback", "complete"]
STEP_LABELS = ["학생 인증", "조건 설정", "문제 생성", "문제 풀이", "피드백", "완료"]
FEEDBACK_FILE = Path("data_files/feedback/feedback.csv")


# ── GNN 모델 ─────────────────────────────────────────────────────────────────

@st.cache_resource
def load_gnn_model():
    return DifficultyPredictor()


# ── 세션 초기화 ───────────────────────────────────────────────────────────────

def initialize_session_state():
    defaults = {
        "session_id": str(uuid.uuid4()),
        "step": "login",
        "student_id": "",
        "questions": [],
        "current_question_index": 0,
        "answers": {},
        "feedback_data": [],
        "gnn_model": load_gnn_model(),
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


initialize_session_state()


# ── 공통 헤더 ─────────────────────────────────────────────────────────────────

def render_step_header():
    """현재 단계에 맞는 진행 상태 표시기를 렌더링."""
    current_idx = STEP_FLOW.index(st.session_state.get("step", "login"))
    step_indicator(STEP_LABELS, current_idx)

    if st.session_state.get("student_id"):
        st.markdown(
            f'<p style="color:#94A3B8;font-size:0.82rem;margin:-0.5rem 0 1rem;">'
            f'학번 <strong style="color:#F8FAFC">{st.session_state.student_id}</strong> '
            f'&nbsp;·&nbsp; 세션 {st.session_state.session_id[:8]}</p>',
            unsafe_allow_html=True,
        )


# ── 피드백 저장 ───────────────────────────────────────────────────────────────

def save_feedback(feedback_data):
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        df = pd.read_csv(FEEDBACK_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "timestamp", "session_id", "student_id", "school_type",
            "question_id", "question", "student_answer", "correct_answer",
            "difficulty_rating", "comment", "unit", "difficulty",
        ])
    df = pd.concat([df, pd.DataFrame([feedback_data])], ignore_index=True)
    df.to_csv(FEEDBACK_FILE, index=False)

    try:
        current_question = st.session_state.questions[st.session_state.current_question_index]
        features = {
            "question": feedback_data["question"],
            "options": current_question["options"],
            "unit": feedback_data["unit"],
        }
        st.session_state.gnn_model.update_training_data(features, feedback_data["difficulty_rating"])
    except Exception as exc:
        st.warning(f"GNN 모델 업데이트 중 오류가 발생했습니다: {exc}")


# ── Step 1: 로그인 ─────────────────────────────────────────────────────────────

def show_login_step():
    hero("🎓", "정보교과 AI 시험 시스템", "AI가 실시간으로 생성하는 개인 맞춤형 문제")

    # 중앙 정렬 로그인 카드
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown('<div class="ex-card">', unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:0.78rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.07em;color:#94A3B8;margin-bottom:0.5rem;">학번 입력</p>',
            unsafe_allow_html=True,
        )
        student_id = st.text_input(
            "학번",
            value=st.session_state.student_id,
            placeholder="예: 2024001",
            label_visibility="collapsed",
        )
        st.markdown("&nbsp;", unsafe_allow_html=True)
        btn = st.button("시험 시작하기", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if btn:
            if student_id.strip():
                st.session_state.student_id = student_id.strip()
                st.session_state.step = "setup"
                st.rerun()
            else:
                st.error("학번을 입력해주세요.")

    # 하단 안내
    st.markdown(
        '<p style="text-align:center;color:#475569;font-size:0.8rem;margin-top:1.5rem;">'
        '입력한 학번은 성적 기록 및 AI 모델 개선에만 사용됩니다.</p>',
        unsafe_allow_html=True,
    )


# ── Step 2: 설정 ──────────────────────────────────────────────────────────────

def show_setup_step():
    render_step_header()
    section("조건 설정", "시험 유형과 난이도를 선택하세요")

    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        st.markdown(
            '<p style="font-size:0.78rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.07em;color:#94A3B8;margin-bottom:0.4rem;">학교 유형</p>',
            unsafe_allow_html=True,
        )
        school_type = st.selectbox(
            "학교 유형",
            ["중학교", "고등학교", "소프트웨어 고등학교"],
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:0.78rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.07em;color:#94A3B8;margin-bottom:0.4rem;">난이도</p>',
            unsafe_allow_html=True,
        )
        difficulty = st.radio(
            "난이도",
            ["하", "중", "상"],
            horizontal=False,
            label_visibility="collapsed",
            captions=["기초 개념 위주", "응용 및 이해", "심화 분석"],
        )

    with col_r:
        st.markdown(
            '<p style="font-size:0.78rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.07em;color:#94A3B8;margin-bottom:0.4rem;">문제 개수</p>',
            unsafe_allow_html=True,
        )
        num_questions = st.slider(
            "문제 개수",
            min_value=3,
            max_value=10,
            step=1,
            value=5,
            label_visibility="collapsed",
        )

        # 미리보기 카드
        diff_badge = difficulty_badge(difficulty)
        school_badges = {
            "중학교": badge("중학교", "p"),
            "고등학교": badge("고등학교", "p"),
            "소프트웨어 고등학교": badge("SW고", "p"),
        }
        st.markdown(f"""
        <div class="ex-card" style="margin-top:1.5rem;">
            <p style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.07em;color:#94A3B8;margin-bottom:0.85rem;">선택 요약</p>
            <div class="ex-info-grid">
                <div class="ex-info-row">
                    <span class="ex-il">학교 유형</span>
                    <span class="ex-iv">{school_badges[school_type]}</span>
                </div>
                <div class="ex-info-row">
                    <span class="ex-il">난이도</span>
                    <span class="ex-iv">{diff_badge}</span>
                </div>
                <div class="ex-info-row">
                    <span class="ex-il">문제 수</span>
                    <span class="ex-iv">{num_questions}문항</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("무료 API 사용 시 5문항 이하 권장")

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, _, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("← 이전", type="secondary", use_container_width=True):
            st.session_state.step = "login"
            st.rerun()
    with col_next:
        if st.button("문제 생성하기 →", type="primary", use_container_width=True):
            st.session_state.difficulty = difficulty
            st.session_state.num_questions = num_questions
            st.session_state.school_type = school_type
            st.session_state.step = "generate"
            st.rerun()


# ── Step 3: 문제 생성 ─────────────────────────────────────────────────────────

def show_generate_step():
    render_step_header()
    section("AI 문제 생성", "선택한 조건으로 맞춤 문제를 생성합니다")

    school_type  = st.session_state.school_type
    difficulty   = st.session_state.difficulty
    num_questions = st.session_state.num_questions

    diff_badge = difficulty_badge(difficulty)
    school_map = {"중학교": badge("중학교", "p"), "고등학교": badge("고등학교", "p"),
                  "소프트웨어 고등학교": badge("SW고", "p")}
    st.markdown(f"""
    <div class="ex-card-accent">
        <div style="display:flex;gap:0.75rem;align-items:center;flex-wrap:wrap;">
            {school_map[school_type]}
            {diff_badge}
            <span class="ex-badge ex-badge-mt">{num_questions}문항</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.questions:
        questions = generate_questions_via_api(difficulty, num_questions, school_type)

        if questions:
            difficulty_order = {"하": 0, "중": 1, "상": 2}
            for q in questions:
                q["predicted_difficulty"] = st.session_state.gnn_model.predict_difficulty(
                    q["question"], q["options"], q["unit"]
                )
            questions.sort(key=lambda x: difficulty_order.get(x["predicted_difficulty"], 1))
            st.session_state.questions = questions

            # 성공 배너
            st.markdown(f"""
            <div class="ex-card-ok">
                <strong style="color:#34D399">✓ {len(questions)}개 문제 생성 완료</strong>
                <p style="margin:0.35rem 0 0;font-size:0.85rem;color:#94A3B8;">
                    GNN 모델이 난이도를 예측하여 순서를 조정했습니다.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # 난이도 분포
            section("예측 난이도 분포")
            dist = pd.DataFrame([{"난이도": q["predicted_difficulty"]} for q in questions])
            counts = dist["난이도"].value_counts().reindex(["하", "중", "상"], fill_value=0)
            st.bar_chart(counts)

            if st.button("문제 풀이 시작하기 →", type="primary"):
                st.session_state.step = "solve"
                st.rerun()
        else:
            st.markdown("""
            <div class="ex-card-er">
                <strong style="color:#F87171">문제 생성에 실패했습니다.</strong>
                <p style="margin:0.35rem 0 0;font-size:0.85rem;color:#94A3B8;">
                    API 키와 네트워크 연결을 확인한 뒤 다시 시도해주세요.
                </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("다시 시도"):
                st.rerun()
    else:
        st.markdown(f"""
        <div class="ex-card-ok">
            <strong style="color:#34D399">✓ {len(st.session_state.questions)}개 문제 준비됨</strong>
        </div>
        """, unsafe_allow_html=True)
        if st.button("문제 풀이 시작하기 →", type="primary"):
            st.session_state.step = "solve"
            st.rerun()


# ── Step 4: 풀이 ──────────────────────────────────────────────────────────────

def show_solve_step():
    render_step_header()

    current_idx    = st.session_state.current_question_index
    total          = len(st.session_state.questions)
    q              = st.session_state.questions[current_idx]

    # 진행 표시
    progress = (current_idx + 1) / total
    st.progress(progress)
    st.markdown(
        f'<p style="font-size:0.8rem;color:#94A3B8;margin:-0.25rem 0 1.25rem;">'
        f'<strong style="color:#F8FAFC">{current_idx + 1}</strong> / {total} 문항 &nbsp;·&nbsp; '
        f'{progress * 100:.0f}% 완료</p>',
        unsafe_allow_html=True,
    )

    col_q, col_info = st.columns([2.2, 1], gap="large")

    with col_q:
        diff_b = difficulty_badge(q["difficulty"])
        st.markdown(f"""
        <div class="ex-card">
            <div class="ex-q-meta">
                <span>Q{current_idx + 1}</span>
                <span>{q["unit"]}</span>
            </div>
            <div style="margin-bottom:0.5rem;">{diff_b}</div>
            <div class="ex-q-text">{q["question"]}</div>
        </div>
        """, unsafe_allow_html=True)

        answer_key = f"answer_{current_idx}"
        selected = st.radio(
            "정답 선택",
            options=q["options"],
            key=answer_key,
            label_visibility="collapsed",
        )
        st.session_state.answers[current_idx] = selected

    with col_info:
        st.markdown(f"""
        <div class="ex-card">
            <p style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.07em;color:#94A3B8;margin-bottom:0.75rem;">문제 정보</p>
            <div class="ex-info-grid">
                <div class="ex-info-row">
                    <span class="ex-il">현재</span>
                    <span class="ex-iv">{current_idx + 1}번</span>
                </div>
                <div class="ex-info-row">
                    <span class="ex-il">남은 문제</span>
                    <span class="ex-iv">{total - current_idx - 1}개</span>
                </div>
                <div class="ex-info-row">
                    <span class="ex-il">완료율</span>
                    <span class="ex-iv">{progress * 100:.0f}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_prev, col_next = st.columns(2)
        with col_prev:
            if current_idx > 0:
                if st.button("← 이전", type="secondary", use_container_width=True):
                    st.session_state.current_question_index -= 1
                    st.rerun()
        with col_next:
            if current_idx < total - 1:
                if st.button("다음 →", type="primary", use_container_width=True):
                    st.session_state.current_question_index += 1
                    st.rerun()
            else:
                if st.button("풀이 완료", type="primary", use_container_width=True):
                    st.session_state.step = "feedback"
                    st.session_state.current_question_index = 0
                    st.rerun()


# ── Step 5: 피드백 ────────────────────────────────────────────────────────────

def show_feedback_step():
    render_step_header()

    current_idx = st.session_state.current_question_index
    total       = len(st.session_state.questions)
    q           = st.session_state.questions[current_idx]

    st.progress((current_idx + 1) / total)
    st.markdown(
        f'<p style="font-size:0.8rem;color:#94A3B8;margin:-0.25rem 0 1.25rem;">'
        f'피드백 <strong style="color:#F8FAFC">{current_idx + 1}</strong> / {total}</p>',
        unsafe_allow_html=True,
    )

    col_q, col_fb = st.columns([2.2, 1], gap="large")

    with col_q:
        section("문제 및 답안 확인")
        diff_b = difficulty_badge(q["difficulty"])
        st.markdown(f"""
        <div class="ex-card">
            <div class="ex-q-meta"><span>Q{current_idx + 1}</span><span>{q["unit"]}</span></div>
            <div style="margin-bottom:0.6rem;">{diff_b}</div>
            <div class="ex-q-text">{q["question"]}</div>
        </div>
        """, unsafe_allow_html=True)

        student_ans = st.session_state.answers.get(current_idx, "")
        correct_ans = q["options"][int(q["answer"]) - 1]
        student_idx = q["options"].index(student_ans) + 1 if student_ans in q["options"] else -1
        is_correct  = student_idx == int(q["answer"])

        if is_correct:
            st.markdown(f"""
            <div class="ex-ans-correct">
                <div class="ex-ans-icon">✓</div>
                <div>
                    <div class="ex-ans-label">정답</div>
                    <div>{correct_ans}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="ex-ans-wrong">
                <div class="ex-ans-icon">✗</div>
                <div>
                    <div class="ex-ans-label">내 답 (오답)</div>
                    <div>{student_ans}</div>
                </div>
            </div>
            <div class="ex-ans-correct">
                <div class="ex-ans-icon">✓</div>
                <div>
                    <div class="ex-ans-label">정답</div>
                    <div>{correct_ans}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_fb:
        section("피드백 작성")
        st.markdown(
            '<p style="font-size:0.78rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.07em;color:#94A3B8;margin-bottom:0.4rem;">난이도 평가 (1~5)</p>',
            unsafe_allow_html=True,
        )
        difficulty_rating = st.radio(
            "난이도 평가",
            [1, 2, 3, 4, 5],
            format_func=lambda x: ["매우 쉬움", "쉬움", "보통", "어려움", "매우 어려움"][x - 1],
            key=f"rating_{current_idx}",
            label_visibility="collapsed",
        )
        comment = st.text_area(
            "의견 (선택)",
            height=90,
            key=f"comment_{current_idx}",
            placeholder="문제에 대한 의견을 남겨주세요.",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_prev, col_sub = st.columns(2)
        with col_prev:
            if current_idx > 0:
                if st.button("← 이전", type="secondary", use_container_width=True):
                    st.session_state.current_question_index -= 1
                    st.rerun()
        with col_sub:
            if st.button("제출 →", type="primary", use_container_width=True):
                feedback_data = {
                    "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "session_id":      st.session_state.session_id,
                    "student_id":      st.session_state.student_id,
                    "school_type":     st.session_state.school_type,
                    "question_id":     q["id"],
                    "question":        q["question"],
                    "student_answer":  student_ans,
                    "correct_answer":  correct_ans,
                    "difficulty_rating": difficulty_rating,
                    "comment":         comment,
                    "unit":            q["unit"],
                    "difficulty":      q["difficulty"],
                }
                st.session_state.feedback_data.append(feedback_data)
                save_feedback(feedback_data)

                if current_idx < total - 1:
                    st.session_state.current_question_index += 1
                    st.rerun()
                else:
                    st.session_state.step = "complete"
                    st.rerun()


# ── Step 6: 완료 ──────────────────────────────────────────────────────────────

def show_complete_step():
    render_step_header()
    st.balloons()

    total = len(st.session_state.questions)
    correct = sum(
        1 for i in range(total)
        if (ans := st.session_state.answers.get(i)) in st.session_state.questions[i]["options"]
        and st.session_state.questions[i]["options"].index(ans) + 1
           == int(st.session_state.questions[i]["answer"])
    )
    accuracy = correct / total * 100 if total else 0

    # 결과 배너
    acc_badge = badge("우수", "ok") if accuracy >= 80 else (badge("보통", "wn") if accuracy >= 50 else badge("노력 필요", "er"))
    st.markdown(f"""
    <div class="ex-hero" style="margin-bottom:1.5rem;">
        <div class="ex-hero-icon">🏆</div>
        <div class="ex-hero-title">시험 완료!</div>
        <p class="ex-hero-sub">모든 문제를 풀고 피드백을 제출했습니다. {acc_badge}</p>
    </div>
    """, unsafe_allow_html=True)

    # 핵심 지표
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 문제 수", total)
    with col2:
        st.metric("정답 수", correct)
    with col3:
        st.metric("정답률", f"{accuracy:.1f}%")

    section("문항별 결과")
    for i, q in enumerate(st.session_state.questions):
        ans = st.session_state.answers.get(i, "")
        correct_opt = q["options"][int(q["answer"]) - 1]
        is_ok = ans in q["options"] and q["options"].index(ans) + 1 == int(q["answer"])
        status_badge = badge("정답", "ok") if is_ok else badge("오답", "er")
        diff_b = difficulty_badge(q["difficulty"])
        st.markdown(f"""
        <div class="ex-card" style="padding:1rem 1.25rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;">
                <span style="font-size:0.78rem;font-weight:700;color:#94A3B8;">Q{i+1} · {q["unit"]}</span>
                <div style="display:flex;gap:0.4rem;">{diff_b} {status_badge}</div>
            </div>
            <p style="font-size:0.88rem;color:#F8FAFC;margin:0.3rem 0;">{q["question"]}</p>
            {"" if is_ok else f'<p style="font-size:0.8rem;color:#F87171;margin:0.2rem 0;">내 답: {ans}</p>'}
            <p style="font-size:0.8rem;color:#34D399;margin:0.2rem 0;">정답: {correct_opt}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("입력하신 피드백은 AI 모델 개선에 활용되어 더 나은 문제를 생성하는 데 도움이 됩니다.")

    if st.button("새로운 시험 시작하기", type="primary"):
        for key in ["questions", "answers", "feedback_data", "current_question_index"]:
            st.session_state.pop(key, None)
        st.session_state.step = "setup"
        st.rerun()


# ── 라우터 ────────────────────────────────────────────────────────────────────

def main():
    step = st.session_state.step
    if step == "login":
        show_login_step()
    elif step == "setup":
        show_setup_step()
    elif step == "generate":
        show_generate_step()
    elif step == "solve":
        show_solve_step()
    elif step == "feedback":
        show_feedback_step()
    elif step == "complete":
        show_complete_step()


if __name__ == "__main__":
    main()
