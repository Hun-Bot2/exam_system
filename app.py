"""Streamlit 기반 학생용 적응형 시험 응시 인터페이스."""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid
from api import generate_questions_via_api
from gnn_model import DifficultyPredictor  # GNN 모델 import

APP_TITLE = "정보교과 시험 문제 출제 시스템"
STEP_FLOW = ["login", "setup", "generate", "solve", "feedback", "complete"]
STEP_LABELS = {
    "login": "학생 인증",
    "setup": "조건 설정",
    "generate": "문제 생성",
    "solve": "문제 풀이",
    "feedback": "피드백 작성",
    "complete": "완료"
}
FEEDBACK_FILE = Path("data_files/feedback/feedback.csv")

# 페이지 설정
st.set_page_config(page_title=APP_TITLE, layout="wide")


def render_app_header(subtitle: Optional[str] = None, show_student_id: bool = True) -> None:
    """공통 페이지 헤더와 단계 진행 상황을 렌더링."""
    st.title(APP_TITLE)
    st.caption("AI 기반 개인 맞춤 문제 생성 시스템")
    render_step_indicator()

    if show_student_id and st.session_state.get("student_id"):
        st.markdown(f"**학번:** {st.session_state.student_id}")

    if subtitle:
        st.header(subtitle)


def render_step_indicator() -> None:
    """현재 단계 진행 상황을 한눈에 보여주는 배지 표시."""
    current_step = st.session_state.get("step", STEP_FLOW[0])
    current_idx = STEP_FLOW.index(current_step)
    badges = []
    for idx, step in enumerate(STEP_FLOW):
        icon = "[완료]" if idx < current_idx else ("[진행중]" if idx == current_idx else "[대기]")
        badges.append(f"{icon} {STEP_LABELS[step]}")
    st.caption(" / ".join(badges))

# GNN 모델 초기화
@st.cache_resource
def load_gnn_model():
    """캐싱된 GNN 난이도 예측기 로드."""
    return DifficultyPredictor()


def initialize_session_state():
    """Streamlit 세션 상태 기본값을 구성."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'step' not in st.session_state:
        st.session_state.step = 'login'  # login -> setup -> generate -> solve -> feedback
    
    if 'student_id' not in st.session_state:
        st.session_state.student_id = ""
        
    if 'questions' not in st.session_state:
        st.session_state.questions = []
        
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
        
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
        
    if 'feedback_data' not in st.session_state:
        st.session_state.feedback_data = []
        
    if 'gnn_model' not in st.session_state:
        st.session_state.gnn_model = load_gnn_model()

initialize_session_state()

def save_feedback(feedback_data):
    """피드백 CSV를 갱신하고 GNN 프로토타입에 학습 데이터를 푸시."""
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = pd.read_csv(FEEDBACK_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            'timestamp', 'session_id', 'student_id', 'school_type',
            'question_id', 'question', 'student_answer', 'correct_answer',
            'difficulty_rating', 'comment', 'unit', 'difficulty'
        ])

    df = pd.concat([df, pd.DataFrame([feedback_data])], ignore_index=True)
    df.to_csv(FEEDBACK_FILE, index=False)

    # 피드백을 즉시 학습 데이터에 반영하여 모델 개선 루프를 시뮬레이션한다.
    try:
        current_question = st.session_state.questions[st.session_state.current_question_index]
        features = {
            'question': feedback_data['question'],
            'options': current_question['options'],
            'unit': feedback_data['unit']
        }
        st.session_state.gnn_model.update_training_data(features, feedback_data['difficulty_rating'])
    except Exception as exc:  # 모델 개발 단계에서는 경고만 노출
        st.warning(f"GNN 모델 업데이트 중 오류가 발생했습니다: {exc}")

# 1단계: 학번 입력
def show_login_step():
    """학생 식별 정보 입력 단계."""
    render_app_header("학생 정보 입력", show_student_id=False)
    st.markdown("---")

    student_id = st.text_input(
        "학번을 입력하세요:", 
        value=st.session_state.student_id,
        placeholder="예: 2024001"
    )
    
    if student_id:
        st.session_state.student_id = student_id
        
        if st.button("다음 단계로 진행", type="primary"):
            st.session_state.step = 'setup'
            st.rerun()
    else:
        st.info("학번을 입력해주세요.")

# 2단계: 문제 생성 조건 설정
def show_setup_step():
    """학생이 시험 조건(난이도, 문항 수 등)을 선택하는 단계."""
    render_app_header("⚙️ 문제 생성 조건 설정")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("난이도 선택")
        difficulty = st.radio(
            "원하는 난이도를 선택하세요",
            options=["하", "중", "상"],
            help="하: 기초 수준, 중: 보통 수준, 상: 고급 수준"
        )
        
    with col2:
        st.subheader("문제 개수")
        num_questions = st.slider(
            "생성할 문제 개수를 선택하세요",
            min_value=3,
            max_value=10,
            step=1,
            value=5
        )
        st.caption("※ 무료 API 키는 5개 이하를 권장합니다.")
    
    st.subheader("학교 유형")
    school_type = st.selectbox(
        "해당하는 학교 유형을 선택하세요",
        options=["중학교", "고등학교", "소프트웨어 고등학교"],
        help="학교 유형에 따라 문제의 수준과 내용이 조정됩니다"
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("이전 단계", type="secondary"):
            st.session_state.step = 'login'
            st.rerun()
    
    with col2:
        if st.button("문제 생성하기", type="primary"):
            # 문제 생성 시작
            st.session_state.difficulty = difficulty
            st.session_state.num_questions = num_questions
            st.session_state.school_type = school_type
            st.session_state.step = 'generate'
            st.rerun()

# 3단계: 문제 생성
def show_generate_step():
    """OpenAI 및 GNN을 사용해 맞춤 문제 세트를 구성."""
    render_app_header("AI 문제 생성 중")
    st.markdown("---")
    
    # 설정 정보 표시
    st.info(f"""
    **생성 조건**
    - 학교 유형: {st.session_state.school_type}
    - 난이도: {st.session_state.difficulty}
    - 문제 개수: {st.session_state.num_questions}개
    """)
    
    # 문제가 아직 생성되지 않았다면 생성
    if not st.session_state.questions:
        questions = generate_questions_via_api(
            st.session_state.difficulty,
            st.session_state.num_questions,
            st.session_state.school_type
        )
        
        if questions:
            # GNN 모델을 사용하여 각 문제의 난이도 예측
            difficulty_order = {'하': 0, '중': 1, '상': 2}
            for question in questions:
                predicted_difficulty = st.session_state.gnn_model.predict_difficulty(
                    question['question'],
                    question['options'],
                    question['unit']
                )
                question['predicted_difficulty'] = predicted_difficulty

            # 예측된 난이도에 따라 문제 정렬 (하→중→상)
            questions.sort(key=lambda x: difficulty_order.get(x['predicted_difficulty'], 1))
            
            st.session_state.questions = questions
            st.success(f"{len(questions)}개의 문제가 성공적으로 생성되었습니다.")
            
            # 난이도 분포 시각화
            difficulty_distribution = pd.DataFrame([
                {'predicted_difficulty': q['predicted_difficulty']} for q in questions
            ])
            
            st.subheader("예측된 난이도 분포")
            st.bar_chart(difficulty_distribution['predicted_difficulty'].value_counts())
            
            if st.button("문제 풀이 시작하기", type="primary"):
                st.session_state.step = 'solve'
                st.rerun()
        else:
            st.error("문제 생성에 실패했습니다. 다시 시도해주세요.")
            if st.button("다시 시도"):
                st.rerun()
    else:
        st.success(f"{len(st.session_state.questions)}개의 문제가 준비되었습니다.")
        if st.button("문제 풀이 시작하기", type="primary"):
            st.session_state.step = 'solve'
            st.rerun()

# 4단계: 문제 풀이
def show_solve_step():
    """학생이 문제를 순차적으로 풀이하는 화면."""
    render_app_header("문제 풀이 진행 중")

    current_idx = st.session_state.current_question_index
    total_questions = len(st.session_state.questions)
    current_question = st.session_state.questions[current_idx]
    
    # 진행률 표시
    progress = (current_idx + 1) / total_questions
    st.progress(progress)
    st.markdown(f"**진행률:** {current_idx + 1}/{total_questions} 문제")
    
    st.markdown("---")
    
    # 문제 표시
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(f"문제 {current_idx + 1}")
        st.markdown(f"**단원:** {current_question['unit']}")
        st.markdown(f"**난이도:** {current_question['difficulty']}")
        st.markdown("---")
        
        st.markdown(f"### {current_question['question']}")
        
        # 객관식 선택지
        answer_key = f"answer_{current_idx}"
        selected_answer = st.radio(
            "정답을 선택하세요:",
            options=current_question['options'],
            key=answer_key
        )
        
        # 답안 저장
        st.session_state.answers[current_idx] = selected_answer
    
    with col2:
        st.markdown("### 문제 정보")
        st.info(f"""
        **현재 문제:** {current_idx + 1}번
        **총 문제 수:** {total_questions}개
        **완료율:** {((current_idx + 1) / total_questions * 100):.1f}%
        """)
        
        # 네비게이션 버튼
        st.markdown("---")
        
        col_prev, col_next = st.columns(2)
        
        with col_prev:
            if current_idx > 0:
                if st.button("⬅️ 이전", type="secondary"):
                    st.session_state.current_question_index -= 1
                    st.rerun()
        
        with col_next:
            if current_idx < total_questions - 1:
                if st.button("다음 ➡️", type="primary"):
                    st.session_state.current_question_index += 1
                    st.rerun()
            else:
                if st.button("풀이 완료", type="primary"):
                    st.session_state.step = 'feedback'
                    st.session_state.current_question_index = 0  # 피드백용 초기화
                    st.rerun()

# 5단계: 피드백 수집
def show_feedback_step():
    """문제별 난이도 평가 및 의견을 수집."""
    render_app_header("문제 피드백 수집")
    
    current_idx = st.session_state.current_question_index
    total_questions = len(st.session_state.questions)
    current_question = st.session_state.questions[current_idx]
    
    # 진행률 표시
    progress = (current_idx + 1) / total_questions
    st.progress(progress)
    st.markdown(f"**피드백 진행률:** {current_idx + 1}/{total_questions} 문제")
    
    st.markdown("---")
    st.header("문제 피드백")
    
    # 문제와 답안 표시
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"문제 {current_idx + 1}")
        st.markdown(f"**단원:** {current_question['unit']}")
        st.markdown(f"**문제:** {current_question['question']}")
        
        # 학생 답안과 정답 비교
        student_answer = st.session_state.answers.get(current_idx, "답안 없음")
        correct_answer = current_question['answer']
        
        # 학생 답안의 인덱스 찾기
        student_answer_idx = current_question['options'].index(student_answer) + 1 if student_answer in current_question['options'] else -1
        
        st.markdown("**답안 비교:**")
        st.write(f"- 내 답안: {student_answer}")
        st.write(f"- 정답: {current_question['options'][int(correct_answer) - 1]}")
        
        if student_answer_idx == int(correct_answer):
            st.success("정답입니다.")
        else:
            st.error("오답입니다.")
    
    with col2:
        st.subheader("난이도 평가")
        difficulty_rating = st.radio(
            "이 문제의 난이도는?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: f"{x}점",
            key=f"rating_{current_idx}"
        )
        
        st.subheader("의견")
        comment = st.text_area(
            "문제에 대한 의견을 남겨주세요",
            height=100,
            key=f"comment_{current_idx}"
        )
    
    # 피드백 제출
    st.markdown("---")
    
    col_prev, col_submit = st.columns([1, 1])
    
    with col_prev:
        if current_idx > 0:
            if st.button("⬅️ 이전 문제", type="secondary"):
                st.session_state.current_question_index -= 1
                st.rerun()
    
    with col_submit:
        if st.button("피드백 제출", type="primary"):
            # 피드백 데이터 저장
            feedback_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'session_id': st.session_state.session_id,
                'student_id': st.session_state.student_id,
                'school_type': st.session_state.school_type,
                'question_id': current_question['id'],
                'question': current_question['question'],
                'student_answer': st.session_state.answers.get(current_idx, "답안 없음"),
                'correct_answer': current_question['options'][int(current_question['answer']) - 1],
                'difficulty_rating': difficulty_rating,
                'comment': comment,
                'unit': current_question['unit'],
                'difficulty': current_question['difficulty']
            }
            
            st.session_state.feedback_data.append(feedback_data)
            save_feedback(feedback_data)
            
            # 다음 문제로 이동 또는 완료
            if current_idx < total_questions - 1:
                st.session_state.current_question_index += 1
                st.success("피드백이 저장되었습니다!")
                st.rerun()
            else:
                # 모든 피드백 완료
                st.session_state.step = 'complete'
                st.rerun()

# 6단계: 완료
def show_complete_step():
    """시험 결과 요약과 다음 학습 안내."""
    render_app_header("시험이 완료되었습니다.")
    st.markdown("---")
    
    st.balloons()
    
    # 결과 요약
    total_questions = len(st.session_state.questions)
    correct_answers = sum(1 for i in range(total_questions) 
                         if st.session_state.answers.get(i) in st.session_state.questions[i]['options'] and 
                         st.session_state.questions[i]['options'].index(st.session_state.answers.get(i)) + 1 == int(st.session_state.questions[i]['answer']))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 문제 수", total_questions)
    
    with col2:
        st.metric("정답 수", correct_answers)
    
    with col3:
        st.metric("정답률", f"{(correct_answers/total_questions*100):.1f}%")
    
    st.markdown("---")
    st.success("모든 피드백이 저장되었습니다. 감사합니다!")
    st.info("이 데이터는 AI 모델 개선에 활용되어 더 나은 문제를 생성하는데 도움이 됩니다.")
    
    if st.button("새로운 시험 시작하기", type="primary"):
        # 세션 초기화
        for key in ['questions', 'answers', 'feedback_data', 'current_question_index']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.step = 'setup'
        st.rerun()

# 메인 앱 실행
def main():
    if st.session_state.step == 'login':
        show_login_step()
    elif st.session_state.step == 'setup':
        show_setup_step()
    elif st.session_state.step == 'generate':
        show_generate_step()
    elif st.session_state.step == 'solve':
        show_solve_step()
    elif st.session_state.step == 'feedback':
        show_feedback_step()
    elif st.session_state.step == 'complete':
        show_complete_step()

if __name__ == "__main__":
    main()
