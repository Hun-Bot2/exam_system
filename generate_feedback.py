"""
실제 사용자 행동 패턴을 시뮬레이션한 피드백 데이터 생성
- 문제 난이도에 따른 학생 반응 모델링
- 학생 수준별 정답률 차이 반영
- 현실적인 난이도 평가 생성
"""

import pandas as pd
import json
import random
import numpy as np
from datetime import datetime, timedelta
import uuid

class FeedbackDataGenerator:
    """피드백 데이터 생성기"""
    
    def __init__(self):
        # 학생 프로필 정의
        self.student_profiles = {
            '상위권': {
                'accuracy_by_difficulty': {'하': 0.95, '중': 0.85, '상': 0.65},
                'rating_bias': -0.5,  # 쉽게 느낌
                'comment_style': 'positive'
            },
            '중위권': {
                'accuracy_by_difficulty': {'하': 0.85, '중': 0.65, '상': 0.40},
                'rating_bias': 0,  # 적정
                'comment_style': 'neutral'
            },
            '하위권': {
                'accuracy_by_difficulty': {'하': 0.60, '중': 0.35, '상': 0.20},
                'rating_bias': 0.8,  # 어렵게 느낌
                'comment_style': 'struggling'
            }
        }
        
        # 난이도에 대한 기본 평가 (1-5)
        self.base_difficulty_rating = {
            '하': 2.0,
            '중': 3.0,
            '상': 4.5
        }
        
        # 코멘트 템플릿
        self.comment_templates = {
            'positive': [
                "쉬웠어요", "이해하기 쉬웠습니다", "적절한 난이도", 
                "잘 풀었어요", "좋은 문제네요"
            ],
            'neutral': [
                "적당했습니다", "괜찮았어요", "보통이에요",
                "이해할만 했어요", "나쁘지 않았어요"
            ],
            'struggling': [
                "어려웠어요", "이해하기 힘들었습니다", "너무 어려워요",
                "다시 공부해야겠어요", "힘들었습니다"
            ]
        }
    
    def generate_student_answer(self, question, student_profile):
        """학생 답안 생성"""
        difficulty = question.get('difficulty', '중')
        accuracy = student_profile['accuracy_by_difficulty'][difficulty]
        
        # 정답 확률에 따라 답안 생성
        is_correct = random.random() < accuracy
        
        if is_correct:
            # 정답 반환
            try:
                answer_idx = int(question['answer']) - 1
                return question['options'][answer_idx]
            except:
                return question['answer']
        else:
            # 오답 반환 (정답이 아닌 랜덤 선택지)
            options = question['options'].copy()
            try:
                answer_idx = int(question['answer']) - 1
                correct = options[answer_idx]
                options.remove(correct)
                return random.choice(options)
            except:
                return random.choice(options)
    
    def generate_difficulty_rating(self, question, student_profile, is_correct):
        """난이도 평가 생성"""
        difficulty = question.get('difficulty', '중')
        base_rating = self.base_difficulty_rating[difficulty]
        bias = student_profile['rating_bias']
        
        # 틀렸으면 더 어렵게 느낌
        correctness_factor = -0.5 if is_correct else 0.5
        
        # 최종 평가 (1-5 범위)
        rating = base_rating + bias + correctness_factor
        rating = max(1, min(5, rating))
        
        # 약간의 랜덤성 추가
        rating += random.uniform(-0.3, 0.3)
        rating = max(1, min(5, rating))
        
        return round(rating)
    
    def generate_comment(self, student_profile, difficulty_rating):
        """코멘트 생성"""
        style = student_profile['comment_style']
        
        # 난이도 평가에 따라 스타일 조정
        if difficulty_rating <= 2:
            style = 'positive'
        elif difficulty_rating >= 4:
            style = 'struggling'
        
        templates = self.comment_templates[style]
        return random.choice(templates)
    
    def generate_feedback_for_question(self, question, num_students=10):
        """한 문제에 대한 여러 학생 피드백 생성"""
        feedbacks = []
        
        for i in range(num_students):
            # 학생 프로필 랜덤 선택 (정규분포: 중위권이 많음)
            profile_type = np.random.choice(
                list(self.student_profiles.keys()),
                p=[0.2, 0.6, 0.2]  # 상위 20%, 중위 60%, 하위 20%
            )
            profile = self.student_profiles[profile_type]
            
            # 학생 답안 생성
            student_answer = self.generate_student_answer(question, profile)
            
            # 정답 여부
            try:
                answer_idx = int(question['answer']) - 1
                correct_answer = question['options'][answer_idx]
            except:
                correct_answer = question['answer']
            
            is_correct = student_answer == correct_answer
            
            # 난이도 평가
            difficulty_rating = self.generate_difficulty_rating(
                question, profile, is_correct
            )
            
            # 코멘트
            comment = self.generate_comment(profile, difficulty_rating)
            
            # 세션 정보
            session_id = str(uuid.uuid4())
            student_id = f"STU{random.randint(1000, 9999)}"
            
            # 타임스탬프 (최근 3개월 내 랜덤)
            days_ago = random.randint(0, 90)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            # 피드백 데이터
            feedback = {
                'timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'session_id': session_id,
                'student_id': student_id,
                'school_type': question.get('school_type', '중학교'),
                'question_id': question['id'],
                'question': question['question'],
                'student_answer': student_answer,
                'correct_answer': correct_answer,
                'difficulty_rating': difficulty_rating,
                'comment': comment,
                'unit': question['unit'],
                'difficulty': question['difficulty']
            }
            
            feedbacks.append(feedback)
        
        return feedbacks
    
    def generate_dataset_feedback(self, questions, students_per_question=10):
        """전체 문제 세트에 대한 피드백 생성"""
        all_feedbacks = []
        
        print(f"피드백 생성 시작: {len(questions)}개 문제")
        print(f"문제당 {students_per_question}명의 학생 피드백 생성")
        
        for idx, question in enumerate(questions):
            if (idx + 1) % 10 == 0:
                print(f"진행중... {idx + 1}/{len(questions)}")
            
            feedbacks = self.generate_feedback_for_question(
                question, students_per_question
            )
            all_feedbacks.extend(feedbacks)
        
        print(f"생성 완료: {len(all_feedbacks)}개 피드백")
        return all_feedbacks
    
    def save_feedback(self, feedbacks, output_file='data_files/feedback/feedback_generated.csv'):
        """피드백 데이터 저장"""
        import os
        
        df = pd.DataFrame(feedbacks)
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 기존 파일이 있으면 병합
        if os.path.exists(output_file):
            existing_df = pd.read_csv(output_file)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"저장 완료: {output_file} ({len(df)}개 레코드)")
        
        return output_file
    
    def generate_statistics(self, feedbacks):
        """생성된 피드백 통계"""
        df = pd.DataFrame(feedbacks)
        
        print("\n" + "="*60)
        print("생성된 피드백 통계")
        print("="*60)
        
        print(f"\n총 피드백 수: {len(df)}")
        
        print("\n난이도별 평균 평가:")
        for diff in ['하', '중', '상']:
            subset = df[df['difficulty'] == diff]
            if len(subset) > 0:
                avg_rating = subset['difficulty_rating'].mean()
                print(f"  {diff}: {avg_rating:.2f} (n={len(subset)})")
        
        print("\n정답률:")
        correct = (df['student_answer'] == df['correct_answer']).sum()
        print(f"  {correct}/{len(df)} ({correct/len(df)*100:.1f}%)")
        
        print("\n난이도별 정답률:")
        for diff in ['하', '중', '상']:
            subset = df[df['difficulty'] == diff]
            if len(subset) > 0:
                correct_subset = (subset['student_answer'] == subset['correct_answer']).sum()
                print(f"  {diff}: {correct_subset}/{len(subset)} ({correct_subset/len(subset)*100:.1f}%)")

# 사용 예시
if __name__ == "__main__":
    import os
    
    print("피드백 데이터 생성 도구")
    print("="*60)
    print("문제 데이터를 기반으로 학생 피드백을 시뮬레이션합니다.")
    print("="*60)
    
    # 파일 선택
    files = {
        '1': 'data_files/questions/middle_school_questions.json',
        '2': 'data_files/questions/software_high_school_questions.json',
        '3': '모두'
    }
    
    print("\n피드백을 생성할 문제 파일 선택:")
    for key, file in files.items():
        print(f"{key}. {file}")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    if choice not in files:
        print("잘못된 선택입니다.")
        exit()
    
    students = input("문제당 학생 수 (기본값: 10): ").strip()
    students = int(students) if students else 10
    
    generator = FeedbackDataGenerator()
    all_feedbacks = []
    
    if choice == '3':
        # 모든 파일 처리
        for key in ['1', '2']:
            file_path = files[key]
            if os.path.exists(file_path):
                print(f"\n처리중: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                # school_type 추가
                school_type = "중학교" if "middle" in file_path else "소프트웨어 고등학교"
                for q in questions:
                    q['school_type'] = school_type
                
                feedbacks = generator.generate_dataset_feedback(questions, students)
                all_feedbacks.extend(feedbacks)
    else:
        # 선택된 파일만 처리
        file_path = files[choice]
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            school_type = "중학교" if "middle" in file_path else "소프트웨어 고등학교"
            for q in questions:
                q['school_type'] = school_type
            
            all_feedbacks = generator.generate_dataset_feedback(questions, students)
        else:
            print(f"파일을 찾을 수 없습니다: {file_path}")
            exit()
    
    # 통계 출력
    generator.generate_statistics(all_feedbacks)
    
    # 저장
    save = input("\n파일로 저장하시겠습니까? (y/n): ")
    if save.lower() == 'y':
        generator.save_feedback(all_feedbacks)
        print("\n완료!")
