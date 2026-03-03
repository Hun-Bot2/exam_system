"""Streamlit 기반 교사용 품질 관리 및 분석 대시보드."""

import os
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from api import generate_questions_via_api

load_dotenv()
TEACHER_PASSWORD = os.getenv("TEACHER_PASSWORD", "teacher2025")

APP_TITLE = "교사용 문제 관리 시스템"
MENU_OPTIONS = [
    "문제 생성 및 검토",
    "학생 피드백 분석",
    "문제 수정 요청",
    "통계 대시보드"
]
MENU_TIPS = {
    "문제 생성 및 검토": "AI가 생성한 문항을 빠르게 검토하고 승인/수정 요청을 남깁니다.",
    "학생 피드백 분석": "학생 난이도 평가와 의견을 바탕으로 품질을 점검합니다.",
    "문제 수정 요청": "교사의 요청 상태를 확인하고 후속 조치를 기록합니다.",
    "통계 대시보드": "난이도 분포, 정답률 추이 등 핵심 지표를 시각화합니다."
}

DATA_FEEDBACK_DIR = Path("data_files/feedback")
FEEDBACK_FILE = DATA_FEEDBACK_DIR / "feedback.csv"
TEACHER_FEEDBACK_FILE = DATA_FEEDBACK_DIR / "teacher_feedback.csv"

DATA_FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


def render_teacher_header(subtitle: str) -> None:
    """교사용 페이지 공통 헤더."""
    st.title(APP_TITLE)
    st.caption("AI 생성 문제의 품질을 검증하고 학습 데이터를 해석하는 관리 도구")
    st.header(subtitle)

def show_teacher_interface():
    """교사용 Streamlit 앱 엔트리 포인트."""
    # 교사 인증 (간단한 패스워드)
    if 'teacher_authenticated' not in st.session_state:
        st.session_state.teacher_authenticated = False
    
    if not st.session_state.teacher_authenticated:
        render_teacher_header("교사 인증")
        password = st.text_input("교사 인증 비밀번호", type="password")
        if st.button("로그인"):
            if password == TEACHER_PASSWORD:
                st.session_state.teacher_authenticated = True
                st.rerun()
            else:
                st.error("잘못된 비밀번호입니다.")
        return
    
    # 메뉴 선택
    menu = st.sidebar.selectbox(
        "메뉴 선택",
        MENU_OPTIONS,
        help="검토 및 분석하고자 하는 영역을 선택하세요."
    )
    st.sidebar.info(MENU_TIPS[menu])
    
    if menu == "문제 생성 및 검토":
        show_question_generation_review()
    elif menu == "학생 피드백 분석":
        show_student_feedback_analysis()
    elif menu == "문제 수정 요청":
        show_question_modification()
    elif menu == "통계 대시보드":
        show_statistics_dashboard()

def show_question_generation_review():
    """문제 생성 및 검토 페이지."""
    render_teacher_header("문제 생성 및 검토")
    
    # 문제 생성 조건 설정
    col1, col2 = st.columns(2)
    
    with col1:
        school_type = st.selectbox("학교 유형", ["중학교", "고등학교", "소프트웨어 고등학교"])
        difficulty = st.selectbox("난이도", ["하", "중", "상"])
        
    with col2:
        num_questions = st.slider("문제 개수", 1, 10, 5)
        unit = st.text_input("특정 단원 (선택사항)", placeholder="예: 알고리즘")
    
    if st.button("문제 생성하기", type="primary"):
        with st.spinner("문제 생성 중..."):
            questions = generate_questions_via_api(difficulty, num_questions, school_type, unit)
            st.session_state.generated_questions = questions or []

    if not st.session_state.get('generated_questions'):
        st.info("생성된 문제가 없습니다. 조건을 지정하고 다시 실행해주세요.")
        return
    
    st.subheader("생성된 문제 검토")
    
    for i, question in enumerate(st.session_state.generated_questions):
        with st.expander(f"문제 {i+1} - {question.get('unit', '단원 미지정')}"):
            st.markdown(f"**문제:** {question['question']}")
            st.markdown("**선택지:**")
            options = question.get('options') or question.get('choices', [])
            for j, choice in enumerate(options, start=1):
                st.markdown(f"{j}. {choice}")
            st.markdown(f"**정답:** {question['answer']}")
            
            # 교사 평가
            col1, col2 = st.columns(2)
            with col1:
                quality_rating = st.select_slider(
                    f"문제 품질 평가 ({i+1}번)",
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    key=f"quality_{i}"
                )
            
            with col2:
                appropriateness = st.select_slider(
                    f"난이도 적절성 ({i+1}번)",
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    key=f"appropriateness_{i}"
                )
            
            teacher_comment = st.text_area(
                f"교사 의견 ({i+1}번)",
                key=f"teacher_comment_{i}",
                height=80
            )
            
            # 수정 요청
            if st.button(f"문제 {i+1} 수정 요청", key=f"modify_{i}"):
                save_teacher_feedback(question, quality_rating, appropriateness, teacher_comment, "수정요청")
                st.success("수정 요청이 저장되었습니다.")
            
            # 승인
            if st.button(f"문제 {i+1} 승인", key=f"approve_{i}", type="primary"):
                save_teacher_feedback(question, quality_rating, appropriateness, teacher_comment, "승인")
                st.success("문제가 승인되었습니다.")

def show_student_feedback_analysis():
    """학생 피드백을 기반으로 품질 지표를 확인."""
    render_teacher_header("학생 피드백 분석")
    
    try:
        feedback_df = pd.read_csv(FEEDBACK_FILE)
        
        if feedback_df.empty:
            st.info("아직 수집된 피드백이 없습니다.")
            return
        
        # 기본 통계
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 응답 수", len(feedback_df))
        
        with col2:
            avg_difficulty = feedback_df['difficulty_rating'].mean()
            st.metric("평균 난이도 평가", f"{avg_difficulty:.2f}")
        
        with col3:
            # 정답률 계산
            correct_answers = (feedback_df['student_answer'] == feedback_df['correct_answer']).sum()
            accuracy = correct_answers / len(feedback_df) * 100
            st.metric("전체 정답률", f"{accuracy:.1f}%")
        
        with col4:
            unique_students = feedback_df['student_id'].nunique()
            st.metric("참여 학생 수", unique_students)
        
        # 상세 분석
        st.subheader("상세 분석")
        
        # 난이도별 분석
        difficulty_analysis = feedback_df.groupby('difficulty', group_keys=False).apply(
            lambda x: pd.Series({
                '평균 난이도 평가': x['difficulty_rating'].mean().round(2),
                '문제 수': len(x),
                '정답 수': (x['student_answer'] == x['correct_answer']).sum()
            }),
            include_groups=False
        )
        
        st.markdown("**난이도별 분석**")
        st.dataframe(difficulty_analysis)
        
        # 단원별 분석
        if 'unit' in feedback_df.columns:
            unit_analysis = feedback_df.groupby('unit', group_keys=False).apply(
                lambda x: pd.Series({
                    '평균 난이도 평가': x['difficulty_rating'].mean().round(2),
                    '정답률(%)': (x['student_answer'] == x['correct_answer']).mean().round(4) * 100
                }),
                include_groups=False
            )
            
            st.markdown("**단원별 분석**")
            st.dataframe(unit_analysis)
        
        # 학생 코멘트 분석
        st.subheader("학생 의견")
        comments = feedback_df[feedback_df['comment'].notna() & (feedback_df['comment'] != '')]
        
        if not comments.empty:
            for _, row in comments.head(10).iterrows():
                st.text_area(
                    f"문제 {row['question_id']} - 학생 {row['student_id']}",
                    value=row['comment'],
                    height=60,
                    disabled=True
                )
        
    except FileNotFoundError:
        st.info("피드백 데이터 파일이 없습니다.")

def show_question_modification():
    """수정 요청 현황을 관리."""
    render_teacher_header("문제 수정 요청")
    
    try:
        teacher_feedback_df = pd.read_csv(TEACHER_FEEDBACK_FILE)
        
        # 수정 요청된 문제들만 필터링
        modification_requests = teacher_feedback_df[
            teacher_feedback_df['status'] == '수정요청'
        ]
        
        if modification_requests.empty:
            st.info("수정 요청된 문제가 없습니다.")
            return
        
        for _, request in modification_requests.iterrows():
            with st.expander(f"수정 요청 - 문제 ID: {request['question_id']}"):
                st.markdown(f"**원본 문제:** {request['original_question']}")
                st.markdown(f"**교사 의견:** {request['teacher_comment']}")
                st.markdown(f"**품질 평가:** {request['quality_rating']}/5")
                st.markdown(f"**난이도 적절성:** {request['appropriateness_rating']}/5")
                
                # 수정된 문제 입력
                modified_question = st.text_area(
                    "수정된 문제",
                    key=f"modified_{request['question_id']}",
                    height=100
                )
                
                if st.button(f"수정 완료", key=f"complete_{request['question_id']}"):
                    # 수정 완료 처리
                    update_modification_status(request['question_id'], modified_question)
                    st.success("수정이 완료되었습니다.")
                    st.rerun()
    
    except FileNotFoundError:
        st.info("교사 피드백 데이터가 없습니다.")

def show_statistics_dashboard():
    """핵심 지표를 요약한 통계 대시보드."""
    render_teacher_header("통계 대시보드")
    
    try:
        feedback_df = pd.read_csv(FEEDBACK_FILE)
        
        if feedback_df.empty:
            st.info("통계를 위한 데이터가 충분하지 않습니다.")
            return
        
        # 시각화
        import plotly.express as px
        import plotly.graph_objects as go
        
        # 난이도별 분포
        col1, col2 = st.columns(2)
        
        with col1:
            difficulty_dist = feedback_df['difficulty'].value_counts()
            fig = px.pie(
                values=difficulty_dist.values,
                names=difficulty_dist.index,
                title="문제 난이도 분포"
            )
            st.plotly_chart(fig)
        
        with col2:
            rating_dist = feedback_df['difficulty_rating'].value_counts().sort_index()
            fig = px.bar(
                x=rating_dist.index,
                y=rating_dist.values,
                title="학생 난이도 평가 분포",
                labels={'x': '난이도 평가', 'y': '응답 수'}
            )
            st.plotly_chart(fig)
        
        # 정답률 추이 (시간별)
        if 'timestamp' in feedback_df.columns:
            feedback_df['timestamp'] = pd.to_datetime(feedback_df['timestamp'])
            feedback_df['date'] = feedback_df['timestamp'].dt.date
            
            daily_accuracy = feedback_df.groupby('date').apply(
                lambda x: (x['student_answer'] == x['correct_answer']).mean() * 100,
                include_groups=False
            ).reset_index()
            daily_accuracy.columns = ['date', 'accuracy']
            
            fig = px.line(
                daily_accuracy,
                x='date',
                y='accuracy',
                title="일별 정답률 추이",
                labels={'accuracy': '정답률 (%)', 'date': '날짜'}
            )
            st.plotly_chart(fig)
    
    except FileNotFoundError:
        st.info("분석할 데이터가 없습니다.")

def save_teacher_feedback(question, quality_rating, appropriateness, comment, status):
    """교사 피드백 저장"""
    try:
        df = pd.read_csv(TEACHER_FEEDBACK_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            'timestamp', 'question_id', 'original_question', 'quality_rating',
            'appropriateness_rating', 'teacher_comment', 'status'
        ])
    
    new_feedback = pd.DataFrame([{
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'question_id': question.get('id', 'unknown'),
        'original_question': question['question'],
        'quality_rating': quality_rating,
        'appropriateness_rating': appropriateness,
        'teacher_comment': comment,
        'status': status
    }])
    
    df = pd.concat([df, new_feedback], ignore_index=True)
    df.to_csv(TEACHER_FEEDBACK_FILE, index=False)

def update_modification_status(question_id, modified_question):
    """수정 상태 업데이트"""
    try:
        df = pd.read_csv(TEACHER_FEEDBACK_FILE)
        df.loc[df['question_id'] == question_id, 'status'] = '수정완료'
        df.loc[df['question_id'] == question_id, 'modified_question'] = modified_question
        df.to_csv(TEACHER_FEEDBACK_FILE, index=False)
    except FileNotFoundError:
        pass


show_teacher_interface()
