"""Streamlit 기반 교사용 품질 관리 및 분석 대시보드."""

import os
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ── 페이지 설정 (반드시 첫 번째 st.* 호출) ──────────────────────────────────
st.set_page_config(
    page_title="교사용 관리 시스템",
    page_icon="🏫",
    layout="wide",
)

from styles import inject_css, hero, section, badge, sidebar_brand, difficulty_badge
inject_css()

from api import generate_questions_via_api

load_dotenv()
TEACHER_PASSWORD = os.getenv("TEACHER_PASSWORD", "teacher2025")

DATA_FEEDBACK_DIR = Path("data_files/feedback")
FEEDBACK_FILE = DATA_FEEDBACK_DIR / "feedback.csv"
TEACHER_FEEDBACK_FILE = DATA_FEEDBACK_DIR / "teacher_feedback.csv"
DATA_FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

# ── 메뉴 정의 ──────────────────────────────────────────────────────────────────
MENU_ICONS = {
    "문제 생성 및 검토": "📝",
    "학생 피드백 분석": "📊",
    "문제 수정 요청":   "✏️",
    "통계 대시보드":    "📈",
    "API 사용 관리":    "⚙️",
}
MENU_TIPS = {
    "문제 생성 및 검토": "AI가 생성한 문항을 빠르게 검토하고 승인/수정 요청을 남깁니다.",
    "학생 피드백 분석":  "학생 난이도 평가와 의견을 바탕으로 품질을 점검합니다.",
    "문제 수정 요청":    "교사의 요청 상태를 확인하고 후속 조치를 기록합니다.",
    "통계 대시보드":     "난이도 분포, 정답률 추이 등 핵심 지표를 시각화합니다.",
    "API 사용 관리":     "API 호출 비용, 캐시 히트율, 레이트 리밋 현황, 문제 풀 재고를 실시간으로 확인합니다.",
}
MENU_OPTIONS = list(MENU_ICONS.keys())


# ── 인증 ───────────────────────────────────────────────────────────────────────

def show_login():
    hero("🏫", "교사용 관리 시스템", "AI 문제 품질 검증 및 학습 데이터 분석 도구")

    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown('<div class="ex-card">', unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:0.78rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.07em;color:#94A3B8;margin-bottom:0.4rem;">교사 인증</p>',
            unsafe_allow_html=True,
        )
        pw = st.text_input("비밀번호", type="password", label_visibility="collapsed",
                           placeholder="교사 인증 비밀번호를 입력하세요")
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("로그인", type="primary", use_container_width=True):
            if pw == TEACHER_PASSWORD:
                st.session_state.teacher_authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
        st.markdown("</div>", unsafe_allow_html=True)


# ── 사이드바 ───────────────────────────────────────────────────────────────────

def render_sidebar() -> str:
    sidebar_brand("교사용", " 관리 시스템", "AI 문제 품질 검증 플랫폼")

    menu = st.sidebar.selectbox(
        "메뉴",
        MENU_OPTIONS,
        format_func=lambda x: f"{MENU_ICONS[x]}  {x}",
        label_visibility="collapsed",
    )
    st.sidebar.markdown(
        f'<div style="background:#334155;border-radius:8px;padding:0.65rem 0.85rem;'
        f'margin-top:0.5rem;font-size:0.8rem;color:#94A3B8;">{MENU_TIPS[menu]}</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("로그아웃", type="secondary", use_container_width=True):
        st.session_state.teacher_authenticated = False
        st.rerun()

    return menu


# ── 페이지 헤더 ────────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "") -> None:
    icon = MENU_ICONS.get(title, "")
    sub = f" — {subtitle}" if subtitle else ""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.75rem;
                margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #475569;">
        <span style="font-size:1.6rem;">{icon}</span>
        <div>
            <h2 style="margin:0;font-size:1.3rem;font-weight:800;color:#F8FAFC;">{title}</h2>
            <p style="margin:0;font-size:0.8rem;color:#94A3B8;">{MENU_TIPS.get(title,"")}{sub}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── 1. 문제 생성 및 검토 ───────────────────────────────────────────────────────

def show_question_generation_review():
    page_header("문제 생성 및 검토")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        school_type = st.selectbox("학교 유형", ["중학교", "고등학교", "소프트웨어 고등학교"])
        difficulty  = st.selectbox("난이도", ["하", "중", "상"])
    with col2:
        num_questions = st.slider("문제 개수", 1, 10, 5)
        unit = st.text_input("특정 단원 (선택)", placeholder="예: 알고리즘")

    if st.button("문제 생성하기", type="primary"):
        with st.spinner("AI가 문제를 생성 중입니다..."):
            questions = generate_questions_via_api(difficulty, num_questions, school_type, unit or None)
            st.session_state.generated_questions = questions or []

    if not st.session_state.get("generated_questions"):
        st.markdown("""
        <div class="ex-card" style="text-align:center;padding:2.5rem;">
            <div style="font-size:2rem;margin-bottom:0.75rem;">📭</div>
            <p style="color:#94A3B8;margin:0;">생성된 문제가 없습니다. 조건을 지정하고 생성해주세요.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    section(f"생성된 문제 검토", f"{len(st.session_state.generated_questions)}개")

    for i, q in enumerate(st.session_state.generated_questions):
        diff_b = difficulty_badge(q.get("difficulty", "중"))
        with st.expander(f"Q{i+1}  ·  {q.get('unit','단원 미지정')}", expanded=False):
            st.markdown(f"""
            <div style="margin-bottom:0.75rem;">{diff_b}</div>
            <div class="ex-q-text" style="margin-bottom:1rem;">{q["question"]}</div>
            """, unsafe_allow_html=True)

            options = q.get("options") or q.get("choices", [])
            correct_idx = int(q["answer"]) - 1
            for j, opt in enumerate(options):
                is_ans = j == correct_idx
                color  = "#34D399" if is_ans else "#94A3B8"
                prefix = "✓" if is_ans else f"{j+1}"
                st.markdown(
                    f'<p style="font-size:0.88rem;color:{color};margin:0.2rem 0;">'
                    f'<strong>{prefix}.</strong> {opt}</p>',
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="ex-divider" style="display:block;height:1px;'
                        'background:#475569;margin:1rem 0;"></div>', unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                quality_rating = st.select_slider(
                    f"문제 품질 ({i+1}번)", options=[1,2,3,4,5], value=3, key=f"quality_{i}")
            with col_b:
                appropriateness = st.select_slider(
                    f"난이도 적절성 ({i+1}번)", options=[1,2,3,4,5], value=3, key=f"appropriateness_{i}")

            teacher_comment = st.text_area(f"교사 의견 ({i+1}번)", key=f"teacher_comment_{i}", height=72)

            col_mod, col_app = st.columns(2)
            with col_mod:
                if st.button(f"수정 요청", key=f"modify_{i}", type="secondary", use_container_width=True):
                    save_teacher_feedback(q, quality_rating, appropriateness, teacher_comment, "수정요청")
                    st.warning("수정 요청이 저장되었습니다.")
            with col_app:
                if st.button(f"승인", key=f"approve_{i}", type="primary", use_container_width=True):
                    save_teacher_feedback(q, quality_rating, appropriateness, teacher_comment, "승인")
                    st.success("문제가 승인되었습니다.")


# ── 2. 학생 피드백 분석 ───────────────────────────────────────────────────────

def show_student_feedback_analysis():
    page_header("학생 피드백 분석")

    try:
        feedback_df = pd.read_csv(FEEDBACK_FILE)
        if feedback_df.empty:
            st.info("아직 수집된 피드백이 없습니다.")
            return
    except FileNotFoundError:
        st.markdown("""
        <div class="ex-card" style="text-align:center;padding:2.5rem;">
            <div style="font-size:2rem;margin-bottom:0.75rem;">📭</div>
            <p style="color:#94A3B8;margin:0;">피드백 데이터 파일이 없습니다.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 응답 수", len(feedback_df))
    with col2:
        avg_d = feedback_df["difficulty_rating"].mean()
        st.metric("평균 난이도 평가", f"{avg_d:.2f}")
    with col3:
        correct = (feedback_df["student_answer"] == feedback_df["correct_answer"]).sum()
        st.metric("전체 정답률", f"{correct / len(feedback_df) * 100:.1f}%")
    with col4:
        st.metric("참여 학생 수", feedback_df["student_id"].nunique())

    section("난이도별 분석")
    difficulty_analysis = feedback_df.groupby("difficulty", group_keys=False).apply(
        lambda x: pd.Series({
            "평균 난이도 평가": x["difficulty_rating"].mean().round(2),
            "문제 수": len(x),
            "정답 수": (x["student_answer"] == x["correct_answer"]).sum(),
        }),
        include_groups=False,
    )
    st.dataframe(difficulty_analysis, use_container_width=True)

    if "unit" in feedback_df.columns:
        section("단원별 분석")
        unit_analysis = feedback_df.groupby("unit", group_keys=False).apply(
            lambda x: pd.Series({
                "평균 난이도 평가": x["difficulty_rating"].mean().round(2),
                "정답률(%)": (x["student_answer"] == x["correct_answer"]).mean().round(4) * 100,
            }),
            include_groups=False,
        )
        st.dataframe(unit_analysis, use_container_width=True)

    section("학생 의견")
    comments = feedback_df[feedback_df["comment"].notna() & (feedback_df["comment"] != "")]
    if not comments.empty:
        for _, row in comments.head(10).iterrows():
            st.markdown(f"""
            <div class="ex-card" style="padding:1rem 1.25rem;margin-bottom:0.6rem;">
                <div style="display:flex;justify-content:space-between;margin-bottom:0.4rem;">
                    <span style="font-size:0.75rem;font-weight:700;color:#6366F1;">
                        문제 {row["question_id"]}</span>
                    <span style="font-size:0.75rem;color:#94A3B8;">학생 {row["student_id"]}</span>
                </div>
                <p style="font-size:0.88rem;color:#E2E8F0;margin:0;">{row["comment"]}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("작성된 의견이 없습니다.")


# ── 3. 문제 수정 요청 ─────────────────────────────────────────────────────────

def show_question_modification():
    page_header("문제 수정 요청")

    try:
        teacher_df = pd.read_csv(TEACHER_FEEDBACK_FILE)
        requests = teacher_df[teacher_df["status"] == "수정요청"]
        if requests.empty:
            st.markdown("""
            <div class="ex-card" style="text-align:center;padding:2.5rem;">
                <div style="font-size:2rem;margin-bottom:0.75rem;">✅</div>
                <p style="color:#94A3B8;margin:0;">수정 요청된 문제가 없습니다.</p>
            </div>
            """, unsafe_allow_html=True)
            return
    except FileNotFoundError:
        st.info("교사 피드백 데이터가 없습니다.")
        return

    section(f"수정 대기 중", f"{len(requests)}건")

    for _, req in requests.iterrows():
        with st.expander(f"문제 ID: {req['question_id']}  ·  품질 {req['quality_rating']}/5"):
            st.markdown(f"""
            <div class="ex-card-accent" style="margin-bottom:0.75rem;">
                <p style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.06em;color:#94A3B8;margin-bottom:0.4rem;">원본 문제</p>
                <p style="color:#F8FAFC;font-size:0.9rem;margin:0;">{req["original_question"]}</p>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(
                    f'<div class="ex-card" style="padding:0.85rem 1rem;">'
                    f'<p style="font-size:0.7rem;font-weight:700;text-transform:uppercase;'
                    f'letter-spacing:0.06em;color:#94A3B8;margin-bottom:0.3rem;">교사 의견</p>'
                    f'<p style="color:#E2E8F0;font-size:0.88rem;margin:0;">{req["teacher_comment"]}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_b:
                st.markdown(
                    f'<div class="ex-card" style="padding:0.85rem 1rem;">'
                    f'<div style="display:flex;gap:1rem;">'
                    f'<div><p style="font-size:0.7rem;font-weight:700;text-transform:uppercase;'
                    f'letter-spacing:0.06em;color:#94A3B8;margin-bottom:0.2rem;">품질</p>'
                    f'<p style="color:#F8FAFC;font-weight:700;margin:0;">{req["quality_rating"]}/5</p></div>'
                    f'<div><p style="font-size:0.7rem;font-weight:700;text-transform:uppercase;'
                    f'letter-spacing:0.06em;color:#94A3B8;margin-bottom:0.2rem;">적절성</p>'
                    f'<p style="color:#F8FAFC;font-weight:700;margin:0;">{req["appropriateness_rating"]}/5</p></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

            modified = st.text_area("수정된 문제", key=f"modified_{req['question_id']}", height=90)
            if st.button("수정 완료", key=f"complete_{req['question_id']}", type="primary"):
                update_modification_status(req["question_id"], modified)
                st.success("수정이 완료되었습니다.")
                st.rerun()


# ── 4. 통계 대시보드 ──────────────────────────────────────────────────────────

def show_statistics_dashboard():
    page_header("통계 대시보드")

    try:
        feedback_df = pd.read_csv(FEEDBACK_FILE)
        if feedback_df.empty:
            st.info("통계를 위한 데이터가 충분하지 않습니다.")
            return
    except FileNotFoundError:
        st.info("분석할 데이터가 없습니다.")
        return

    import plotly.express as px

    col1, col2 = st.columns(2, gap="large")

    with col1:
        section("문제 난이도 분포")
        difficulty_dist = feedback_df["difficulty"].value_counts()
        fig = px.pie(
            values=difficulty_dist.values,
            names=difficulty_dist.index,
            color_discrete_sequence=["#6366F1", "#34D399", "#F87171"],
            hole=0.45,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0", showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#94A3B8"),
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section("학생 난이도 평가 분포")
        rating_dist = feedback_df["difficulty_rating"].value_counts().sort_index()
        fig = px.bar(
            x=rating_dist.index,
            y=rating_dist.values,
            labels={"x": "난이도 평가", "y": "응답 수"},
            color_discrete_sequence=["#6366F1"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0",
            xaxis=dict(showgrid=False, color="#94A3B8"),
            yaxis=dict(gridcolor="#334155", color="#94A3B8"),
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    if "timestamp" in feedback_df.columns:
        section("일별 정답률 추이")
        feedback_df["timestamp"] = pd.to_datetime(feedback_df["timestamp"])
        feedback_df["date"] = feedback_df["timestamp"].dt.date
        daily_acc = feedback_df.groupby("date").apply(
            lambda x: (x["student_answer"] == x["correct_answer"]).mean() * 100,
            include_groups=False,
        ).reset_index()
        daily_acc.columns = ["date", "accuracy"]
        fig = px.line(
            daily_acc, x="date", y="accuracy",
            labels={"accuracy": "정답률 (%)", "date": "날짜"},
            color_discrete_sequence=["#6366F1"],
            markers=True,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0",
            xaxis=dict(showgrid=False, color="#94A3B8"),
            yaxis=dict(gridcolor="#334155", color="#94A3B8", range=[0, 105]),
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)


# ── 5. API 사용 관리 ──────────────────────────────────────────────────────────

def show_api_usage_management():
    page_header("API 사용 관리")

    from api import _get_cache, SCHOOL_CONFIG, _build_prompt, _call_backend_api
    cache = _get_cache()

    if not cache.is_available():
        st.markdown("""
        <div class="ex-card-er">
            <strong style="color:#F87171">Redis에 연결할 수 없습니다.</strong>
            <p style="margin:0.35rem 0 0;font-size:0.85rem;color:#94A3B8;">
                <code>docker-compose up -d</code> 로 Redis를 시작하세요.
                Redis 없이도 앱은 정상 동작하지만, 캐시·통계 기능은 비활성화됩니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── 오늘 지표 ──────────────────────────────────────────────────
    section("오늘의 API 사용 현황")
    today = cache.get_daily_stats()

    cost_usd = today["api_calls"] * 0.0005
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("오늘 API 호출 수", today["api_calls"])
    with col2:
        st.metric("예상 비용 (오늘)", f"${cost_usd:.4f}",
                  delta=f"≈ ₩{cost_usd * 1350:,.0f}")
    with col3:
        st.metric("캐시 히트율", f"{today['hit_rate']:.1f}%")
    with col4:
        st.metric("총 제공 문제 수", today["total_served"])

    # ── 주간 추이 ──────────────────────────────────────────────────
    section("최근 7일 추이")
    weekly = cache.get_weekly_stats()
    week_api = sum(d["api_calls"] for d in weekly)
    week_usd = week_api * 0.0005

    col1, col2 = st.columns(2)
    with col1:
        st.metric("7일 API 호출 합계", week_api)
    with col2:
        st.metric("7일 예상 비용", f"${week_usd:.4f}", delta=f"≈ ₩{week_usd * 1350:,.0f}")

    if weekly:
        chart = pd.DataFrame(weekly[::-1]).set_index("date")[["api_calls", "cache_hits"]]
        chart.columns = ["API 호출", "캐시 히트"]
        st.line_chart(chart)

    # ── 레이트 리밋 ────────────────────────────────────────────────
    section("레이트 리밋 현황")
    rl = cache.get_rate_limit_status()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("이번 분 호출", f"{rl['current_minute']}/14")
    with col2:
        st.metric("다음 리셋까지", f"{rl['seconds_to_reset']}초")
    with col3:
        st.metric("오늘 누적 호출", rl["daily_total"])

    from cache import RATE_LIMIT_MINUTE
    ratio = min(rl["current_minute"] / RATE_LIMIT_MINUTE, 1.0)
    st.progress(ratio)
    if rl["current_minute"] >= RATE_LIMIT_MINUTE:
        st.warning("레이트 리밋에 도달했습니다. 새 요청은 다음 분까지 자동 대기합니다.")

    # ── 풀 재고 ────────────────────────────────────────────────────
    section("문제 풀 재고")
    pool_sizes = cache.get_all_pool_sizes()

    difficulties = ["하", "중", "상"]
    pool_df = pd.DataFrame(
        {school: [pool_sizes[school][d] for d in difficulties] for school in pool_sizes},
        index=difficulties,
    ).T
    pool_df.index.name = "학교 유형"

    def _color_cell(val):
        if val >= 20:
            return "background-color: rgba(52,211,153,0.12); color: #34D399"
        elif val >= 10:
            return "background-color: rgba(252,211,77,0.12); color: #FCD34D"
        return "background-color: rgba(248,113,113,0.12); color: #F87171"

    st.dataframe(pool_df.style.applymap(_color_cell), use_container_width=True)
    st.caption("초록 ≥20 · 노랑 10~19 · 빨강 <10")

    # ── 풀 예열 ────────────────────────────────────────────────────
    section("문제 풀 예열", "모든 조합에 문제를 미리 채웁니다")
    st.markdown(
        '<div class="ex-card-warn"><p style="margin:0;font-size:0.88rem;color:#E2E8F0;">'
        '예열을 실행하면 학교 유형 × 난이도 9개 조합에 미리 문제를 생성합니다. '
        '레이트 리밋을 자동으로 준수하여 순서대로 실행됩니다.</p></div>',
        unsafe_allow_html=True,
    )

    from cache import POOL_MIN, POOL_REPLENISH
    if st.button("풀 예열 시작", type="primary"):
        combos = [(s, d) for s in SCHOOL_CONFIG for d in ["하", "중", "상"]]
        total = len(combos)
        bar = st.progress(0)
        status = st.empty()

        for idx, (school_type, diff) in enumerate(combos):
            cur = cache.pool_size(school_type, diff, None)
            if cur >= POOL_MIN:
                status.markdown(
                    f'<p style="font-size:0.82rem;color:#94A3B8;">({idx+1}/{total}) '
                    f'{school_type} / {diff} — 풀 충분 ({cur}개), 건너뜀</p>',
                    unsafe_allow_html=True,
                )
                bar.progress((idx + 1) / total)
                continue

            status.markdown(
                f'<p style="font-size:0.82rem;color:#F8FAFC;">({idx+1}/{total}) '
                f'{school_type} / {diff} — 생성 중...</p>',
                unsafe_allow_html=True,
            )
            try:
                cache.check_and_increment_rate_limit()
                prompt = _build_prompt(diff, POOL_REPLENISH, school_type, None)
                cache.increment_api_calls()
                qs = _call_backend_api(prompt, school_type, POOL_REPLENISH)
                if qs:
                    cache.push_to_pool(school_type, diff, None, qs)
            except Exception as exc:
                st.warning(f"{school_type}/{diff} 오류: {exc}")
            bar.progress((idx + 1) / total)

        st.success("풀 예열 완료!")

    if st.button("새로고침", type="secondary"):
        st.rerun()


# ── 데이터 헬퍼 ───────────────────────────────────────────────────────────────

def save_teacher_feedback(question, quality_rating, appropriateness, comment, status):
    try:
        df = pd.read_csv(TEACHER_FEEDBACK_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "timestamp", "question_id", "original_question", "quality_rating",
            "appropriateness_rating", "teacher_comment", "status",
        ])
    new_row = pd.DataFrame([{
        "timestamp":            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question_id":          question.get("id", "unknown"),
        "original_question":    question["question"],
        "quality_rating":       quality_rating,
        "appropriateness_rating": appropriateness,
        "teacher_comment":      comment,
        "status":               status,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(TEACHER_FEEDBACK_FILE, index=False)


def update_modification_status(question_id, modified_question):
    try:
        df = pd.read_csv(TEACHER_FEEDBACK_FILE)
        df.loc[df["question_id"] == question_id, "status"] = "수정완료"
        df.loc[df["question_id"] == question_id, "modified_question"] = modified_question
        df.to_csv(TEACHER_FEEDBACK_FILE, index=False)
    except FileNotFoundError:
        pass


# ── 엔트리 포인트 ─────────────────────────────────────────────────────────────

def show_teacher_interface():
    if "teacher_authenticated" not in st.session_state:
        st.session_state.teacher_authenticated = False

    if not st.session_state.teacher_authenticated:
        show_login()
        return

    menu = render_sidebar()

    if menu == "문제 생성 및 검토":
        show_question_generation_review()
    elif menu == "학생 피드백 분석":
        show_student_feedback_analysis()
    elif menu == "문제 수정 요청":
        show_question_modification()
    elif menu == "통계 대시보드":
        show_statistics_dashboard()
    elif menu == "API 사용 관리":
        show_api_usage_management()


show_teacher_interface()
