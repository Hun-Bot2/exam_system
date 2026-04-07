"""공유 디자인 시스템 — CSS 인젝션 및 HTML 컴포넌트."""

import streamlit as st

# ── Design tokens ──────────────────────────────────────────────────────────────
BG     = "#0F172A"   # 배경 (slate-900)
S1     = "#1E293B"   # 카드 표면 (slate-800)
S2     = "#334155"   # 입력 배경 (slate-700)
BR     = "#475569"   # 테두리 (slate-600)
P      = "#6366F1"   # 주요 색 (indigo-500)
PL     = "#818CF8"   # 주요 색 밝음 (indigo-400)
TX     = "#F8FAFC"   # 텍스트 (slate-50)
TM     = "#94A3B8"   # 보조 텍스트 (slate-400)
OK     = "#34D399"   # 성공 (emerald-400)
WN     = "#FCD34D"   # 경고 (amber-300)
ER     = "#F87171"   # 오류 (red-400)

# ── Global CSS ─────────────────────────────────────────────────────────────────
_CSS = """
<style>
/* ── Reset ──────────────────────────────────────────────── */
.stApp {{ background-color: {BG} !important; }}
#MainMenu, footer {{ display: none !important; }}
[data-testid="stHeader"] {{ background-color: {BG} !important; border-bottom: 1px solid {BR}; }}
[data-testid="stToolbar"] {{ display: none !important; }}

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: {S1} !important;
    border-right: 1px solid {BR} !important;
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
    color: {TM} !important;
    font-size: 0.85rem !important;
}}

/* ── Text inputs ──────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea textarea {{
    background-color: {S2} !important;
    border: 1px solid {BR} !important;
    border-radius: 8px !important;
    color: {TX} !important;
    font-size: 0.95rem !important;
    padding: 0.55rem 0.85rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {{
    border-color: {P} !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18) !important;
    outline: none !important;
}}

/* ── Select box ──────────────────────────────────────────── */
.stSelectbox > div > div {{
    background-color: {S2} !important;
    border: 1px solid {BR} !important;
    border-radius: 8px !important;
    color: {TX} !important;
}}

/* ── Radio buttons ───────────────────────────────────────── */
.stRadio > div {{
    gap: 0.45rem !important;
    flex-direction: column !important;
}}
.stRadio > div > label {{
    background-color: {S2} !important;
    border: 1px solid {BR} !important;
    border-radius: 8px !important;
    padding: 0.6rem 1rem !important;
    color: {TM} !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: border-color 0.15s, background 0.15s !important;
    width: 100% !important;
    margin: 0 !important;
}}
.stRadio > div > label:hover {{
    border-color: {P} !important;
    color: {TX} !important;
}}
.stRadio > div > label[data-checked="true"],
.stRadio > div > label:has(input:checked) {{
    border-color: {P} !important;
    background-color: rgba(99, 102, 241, 0.12) !important;
    color: {PL} !important;
}}

/* ── Slider ──────────────────────────────────────────────── */
.stSlider [data-baseweb="slider"] {{ padding-bottom: 0.5rem !important; }}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button {{
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.01em !important;
    padding: 0.5rem 1.25rem !important;
    transition: all 0.2s !important;
    white-space: nowrap !important;
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {P} 0%, #4F46E5 100%) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 2px 10px rgba(99, 102, 241, 0.35) !important;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 18px rgba(99, 102, 241, 0.5) !important;
}}
.stButton > button[kind="secondary"] {{
    background: transparent !important;
    border: 1px solid {BR} !important;
    color: {TM} !important;
}}
.stButton > button[kind="secondary"]:hover {{
    border-color: {P} !important;
    color: {PL} !important;
    background: rgba(99, 102, 241, 0.06) !important;
}}

/* ── Progress bar ────────────────────────────────────────── */
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, {P}, {PL}) !important;
    border-radius: 4px !important;
}}
.stProgress > div > div > div {{
    background: {S2} !important;
    border-radius: 4px !important;
    height: 6px !important;
}}

/* ── Metrics ─────────────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: {S1} !important;
    border: 1px solid {BR} !important;
    border-radius: 12px !important;
    padding: 1.1rem 1.25rem !important;
}}
[data-testid="stMetricLabel"] > div {{
    color: {TM} !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}}
[data-testid="stMetricValue"] > div {{
    color: {TX} !important;
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    line-height: 1.1 !important;
}}
[data-testid="stMetricDelta"] svg {{ display: none !important; }}
[data-testid="stMetricDelta"] > div {{
    font-size: 0.78rem !important;
    color: {TM} !important;
}}

/* ── Expanders ───────────────────────────────────────────── */
details {{
    background: {S1} !important;
    border: 1px solid {BR} !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    margin-bottom: 0.6rem !important;
}}
summary {{
    color: {TX} !important;
    font-weight: 600 !important;
    padding: 0.85rem 1.1rem !important;
    font-size: 0.92rem !important;
}}
details[open] > summary {{
    border-bottom: 1px solid {BR} !important;
}}

/* ── Alerts & notices ────────────────────────────────────── */
[data-testid="stAlert"] {{
    border-radius: 10px !important;
    font-size: 0.88rem !important;
}}

/* ── Charts / dataframe ──────────────────────────────────── */
.stDataFrame {{ border: 1px solid {BR} !important; border-radius: 10px !important; overflow: hidden !important; }}
[data-testid="stArrowVegaLiteChart"],
[data-testid="stVegaLiteChart"] {{
    background: {S1} !important;
    border: 1px solid {BR} !important;
    border-radius: 12px !important;
    padding: 0.5rem !important;
}}

/* ── Spinner ─────────────────────────────────────────────── */
[data-testid="stSpinner"] > div > div {{
    border-top-color: {P} !important;
}}

/* ─────────────────────────────────────────────────────────── */
/* Custom component classes                                    */
/* ─────────────────────────────────────────────────────────── */

/* Hero banner */
.ex-hero {{
    background: linear-gradient(145deg, {S1} 0%, rgba(99,102,241,0.07) 100%);
    border: 1px solid {BR};
    border-radius: 18px;
    padding: 2.75rem 2.5rem;
    text-align: center;
    margin-bottom: 2rem;
}}
.ex-hero-icon {{ font-size: 3.2rem; line-height: 1; margin-bottom: 0.9rem; }}
.ex-hero-title {{
    font-size: 1.95rem;
    font-weight: 800;
    background: linear-gradient(135deg, {TX} 20%, {PL} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    margin: 0 0 0.55rem;
    line-height: 1.15;
}}
.ex-hero-sub {{ color: {TM}; font-size: 0.95rem; margin: 0; line-height: 1.5; }}

/* Section heading */
.ex-section {{
    display: flex;
    align-items: baseline;
    gap: 0.65rem;
    margin: 1.75rem 0 1rem;
    padding-bottom: 0.65rem;
    border-bottom: 1px solid {BR};
}}
.ex-section-title {{
    font-size: 0.98rem;
    font-weight: 700;
    color: {TX};
    margin: 0;
}}
.ex-section-sub {{
    font-size: 0.8rem;
    color: {TM};
    margin: 0;
}}

/* Cards */
.ex-card {{
    background: {S1};
    border: 1px solid {BR};
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}}
.ex-card-accent {{
    background: {S1};
    border: 1px solid {BR};
    border-left: 4px solid {P};
    border-radius: 0 12px 12px 0;
    padding: 1.4rem 1.5rem;
    margin-bottom: 1rem;
}}
.ex-card-ok {{
    background: rgba(52,211,153,0.05);
    border: 1px solid rgba(52,211,153,0.25);
    border-left: 4px solid {OK};
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.3rem;
    margin-bottom: 0.75rem;
}}
.ex-card-er {{
    background: rgba(248,113,113,0.05);
    border: 1px solid rgba(248,113,113,0.25);
    border-left: 4px solid {ER};
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.3rem;
    margin-bottom: 0.75rem;
}}
.ex-card-warn {{
    background: rgba(252,211,77,0.05);
    border: 1px solid rgba(252,211,77,0.25);
    border-left: 4px solid {WN};
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.3rem;
    margin-bottom: 0.75rem;
}}

/* Badges */
.ex-badge {{
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    line-height: 1.4;
}}
.ex-badge-p  {{ background: rgba(99,102,241,0.15); color: {PL}; }}
.ex-badge-ok {{ background: rgba(52,211,153,0.15); color: {OK}; }}
.ex-badge-wn {{ background: rgba(252,211,77,0.15);  color: {WN}; }}
.ex-badge-er {{ background: rgba(248,113,113,0.15); color: {ER}; }}
.ex-badge-mt {{ background: {S2}; color: {TM}; }}

/* Step indicator */
.ex-steps {{
    display: flex;
    align-items: center;
    padding: 1.1rem 0 1.6rem;
    overflow-x: auto;
    gap: 0;
}}
.ex-step {{
    display: flex;
    align-items: center;
    gap: 0.45rem;
    flex-shrink: 0;
}}
.ex-step-circle {{
    width: 28px; height: 28px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.68rem; font-weight: 800;
    flex-shrink: 0;
}}
.ex-step-done   .ex-step-circle {{ background: {OK}; color: #064e3b; }}
.ex-step-active .ex-step-circle {{ background: {P}; color: #fff; box-shadow: 0 0 0 4px rgba(99,102,241,0.25); }}
.ex-step-wait   .ex-step-circle {{ background: {S2}; color: {TM}; border: 1.5px solid {BR}; }}
.ex-step-label {{ font-size: 0.78rem; font-weight: 600; white-space: nowrap; }}
.ex-step-done   .ex-step-label {{ color: {OK}; }}
.ex-step-active .ex-step-label {{ color: {TX}; }}
.ex-step-wait   .ex-step-label {{ color: {TM}; }}
.ex-step-line {{ width: 28px; height: 2px; background: {BR}; margin: 0 0.15rem; flex-shrink: 0; }}
.ex-step-line-done {{ background: {OK}; }}

/* Question display */
.ex-q-meta {{
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: {P};
    margin-bottom: 0.65rem;
}}
.ex-q-meta span {{ margin-right: 0.75rem; }}
.ex-q-text {{
    font-size: 1.1rem;
    font-weight: 600;
    color: {TX};
    line-height: 1.65;
}}

/* Info grid */
.ex-info-grid {{ display: grid; gap: 0.35rem; }}
.ex-info-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
    padding: 0.4rem 0;
    border-bottom: 1px solid {BR};
}}
.ex-info-row:last-child {{ border-bottom: none; }}
.ex-il {{ color: {TM}; font-weight: 500; }}
.ex-iv {{ color: {TX}; font-weight: 600; }}

/* Stat mini block */
.ex-stat-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }}
.ex-stat {{
    background: {S2};
    border-radius: 10px;
    padding: 0.9rem 1rem;
    text-align: center;
}}
.ex-stat-val {{
    font-size: 1.5rem; font-weight: 700; color: {TX}; line-height: 1; margin-bottom: 0.3rem;
}}
.ex-stat-lbl {{
    font-size: 0.68rem; font-weight: 700; color: {TM}; text-transform: uppercase; letter-spacing: 0.06em;
}}

/* Sidebar brand */
.ex-brand {{
    padding: 1.1rem 0.5rem 1rem;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid {BR};
}}
.ex-brand-name {{
    font-size: 1.05rem; font-weight: 800; color: {TX}; letter-spacing: -0.02em;
}}
.ex-brand-name span {{ color: {PL}; }}
.ex-brand-sub {{
    font-size: 0.7rem; color: {TM}; margin-top: 0.2rem;
}}

/* Login card */
.ex-login-wrap {{
    max-width: 420px;
    margin: 2rem auto;
}}

/* Divider with label */
.ex-divider {{
    display: flex; align-items: center; gap: 0.75rem;
    margin: 1.5rem 0;
    color: {TM}; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;
}}
.ex-divider::before, .ex-divider::after {{
    content: ""; flex: 1; height: 1px; background: {BR};
}}

/* Result answer display */
.ex-ans-correct {{
    display: flex; align-items: flex-start; gap: 0.75rem;
    background: rgba(52,211,153,0.07); border: 1px solid rgba(52,211,153,0.25);
    border-radius: 10px; padding: 0.9rem 1.1rem; margin-bottom: 0.5rem;
    font-size: 0.9rem; color: {TX};
}}
.ex-ans-wrong {{
    display: flex; align-items: flex-start; gap: 0.75rem;
    background: rgba(248,113,113,0.07); border: 1px solid rgba(248,113,113,0.25);
    border-radius: 10px; padding: 0.9rem 1.1rem; margin-bottom: 0.5rem;
    font-size: 0.9rem; color: {TX};
}}
.ex-ans-icon {{ font-size: 1.1rem; flex-shrink: 0; margin-top: 0.05rem; }}
.ex-ans-label {{ font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.2rem; }}
.ex-ans-correct .ex-ans-label {{ color: {OK}; }}
.ex-ans-wrong   .ex-ans-label {{ color: {ER}; }}
</style>
""".format(BG=BG, S1=S1, S2=S2, BR=BR, P=P, PL=PL, TX=TX, TM=TM, OK=OK, WN=WN, ER=ER)


# ── Public API ─────────────────────────────────────────────────────────────────

def inject_css() -> None:
    """전역 CSS를 현재 Streamlit 앱에 주입합니다. 각 페이지 파일 최상단에서 호출하세요."""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(icon: str, title: str, subtitle: str = "") -> None:
    sub = f'<p class="ex-hero-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="ex-hero">
        <div class="ex-hero-icon">{icon}</div>
        <div class="ex-hero-title">{title}</div>
        {sub}
    </div>
    """, unsafe_allow_html=True)


def section(title: str, subtitle: str = "") -> None:
    sub = f'<span class="ex-section-sub">— {subtitle}</span>' if subtitle else ""
    st.markdown(f"""
    <div class="ex-section">
        <span class="ex-section-title">{title}</span>
        {sub}
    </div>
    """, unsafe_allow_html=True)


def badge(text: str, kind: str = "p") -> str:
    """인라인 배지 HTML 반환. kind: p | ok | wn | er | mt"""
    return f'<span class="ex-badge ex-badge-{kind}">{text}</span>'


def card(html: str, accent: bool = False) -> None:
    cls = "ex-card-accent" if accent else "ex-card"
    st.markdown(f'<div class="{cls}">{html}</div>', unsafe_allow_html=True)


def step_indicator(labels: list, current_idx: int) -> None:
    """진행 단계 표시기.

    labels: 단계 레이블 리스트 (순서대로)
    current_idx: 현재 활성 단계 인덱스 (0-based)
    """
    parts = []
    for i, label in enumerate(labels):
        if i < current_idx:
            cls, circle = "ex-step-done", "✓"
        elif i == current_idx:
            cls, circle = "ex-step-active", str(i + 1)
        else:
            cls, circle = "ex-step-wait", str(i + 1)

        if i > 0:
            line_cls = "ex-step-line ex-step-line-done" if i <= current_idx else "ex-step-line"
            parts.append(f'<div class="{line_cls}"></div>')

        parts.append(f"""
        <div class="ex-step {cls}">
            <div class="ex-step-circle">{circle}</div>
            <span class="ex-step-label">{label}</span>
        </div>
        """)

    st.markdown(f'<div class="ex-steps">{"".join(parts)}</div>', unsafe_allow_html=True)


def sidebar_brand(name: str, highlight: str, sub: str) -> None:
    """사이드바 브랜드 헤더."""
    st.sidebar.markdown(f"""
    <div class="ex-brand">
        <div class="ex-brand-name">{name}<span>{highlight}</span></div>
        <div class="ex-brand-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def difficulty_badge(level: str) -> str:
    mapping = {"하": ("ok", "하"), "중": ("wn", "중"), "상": ("er", "상")}
    kind, text = mapping.get(level, ("mt", level))
    return badge(text, kind)
