"""OpenAI API를 활용해 문제 은행을 대량 확장하는 CLI 스크립트."""

import json
import time
from api import generate_questions_via_api
from datetime import datetime
import os

class QuestionDataExpander:
    """문제 데이터 확장 클래스"""
    
    def __init__(self):
        self.school_types = ["중학교", "고등학교", "소프트웨어 고등학교"]
        self.difficulty_levels = ["하", "중", "상"]
        self.units = {
            "중학교": [
                "컴퓨팅 시스템", "자료와 정보", "알고리즘과 프로그래밍",
                "컴퓨팅과 문제해결", "디지털 문화"
            ],
            "고등학교": [
                "프로그래밍 기초", "알고리즘 설계", "자료구조",
                "데이터베이스", "네트워크", "정보보안"
            ],
            "소프트웨어 고등학교": [
                "프로그래밍 기초", "고급 프로그래밍", "알고리즘과 자료구조",
                "소프트웨어 개발", "데이터베이스 설계", "네트워크 프로그래밍"
            ]
        }
    
    def generate_batch_questions(self, school_type, difficulty, unit, batch_size=5):
        """배치 단위로 문제 생성"""
        print(f"생성 중: {school_type} - {difficulty} - {unit} ({batch_size}개)")
        
        try:
            questions = generate_questions_via_api(
                student_level=difficulty,
                num_questions=batch_size,
                school_type=school_type,
                unit=unit
            )
            
            if questions:
                print(f"✓ {len(questions)}개 생성 완료")
                return questions
            else:
                print(f"✗ 생성 실패")
                return []
                
        except Exception as e:
            print(f"✗ 에러 발생: {str(e)}")
            return []
    
    def expand_questions(self, target_per_school=300, batch_size=5, delay=2):
        """
        대량 문제 생성
        
        Args:
            target_per_school: 학교 유형당 목표 문제 수
            batch_size: 한 번에 생성할 문제 수
            delay: API 호출 간 대기 시간(초)
        """
        all_questions = {
            "중학교": [],
            "고등학교": [],
            "소프트웨어 고등학교": []
        }
        
        total_generated = 0
        
        for school_type in self.school_types:
            print(f"\n{'='*60}")
            print(f"{school_type} 문제 생성 시작")
            print(f"{'='*60}")
            
            school_questions = []
            units = self.units[school_type]
            
            # 단원별로 균등 분배
            questions_per_unit = target_per_school // len(units)
            
            for unit in units:
                unit_questions = []
                
                # 난이도별로 균등 분배
                questions_per_difficulty = questions_per_unit // len(self.difficulty_levels)
                
                for difficulty in self.difficulty_levels:
                    # 배치 단위로 생성
                    num_batches = questions_per_difficulty // batch_size
                    remaining = questions_per_difficulty % batch_size
                    
                    # 배치 생성
                    for batch in range(num_batches):
                        questions = self.generate_batch_questions(
                            school_type, difficulty, unit, batch_size
                        )
                        unit_questions.extend(questions)
                        total_generated += len(questions)
                        
                        # API 호출 제한 방지
                        time.sleep(delay)
                    
                    # 남은 문제 생성
                    if remaining > 0:
                        questions = self.generate_batch_questions(
                            school_type, difficulty, unit, remaining
                        )
                        unit_questions.extend(questions)
                        total_generated += len(questions)
                        time.sleep(delay)
                
                school_questions.extend(unit_questions)
                print(f"  {unit}: {len(unit_questions)}개 완료")
            
            all_questions[school_type] = school_questions
            print(f"\n{school_type} 총 {len(school_questions)}개 생성 완료")
        
        print(f"\n{'='*60}")
        print(f"전체 생성 완료: 총 {total_generated}개")
        print(f"{'='*60}")
        
        return all_questions
    
    def save_questions(self, questions_dict):
        """생성된 문제를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for school_type, questions in questions_dict.items():
            if not questions:
                continue
            
            # 기존 파일과 병합
            existing_questions = self.load_existing_questions(school_type)
            merged_questions = existing_questions + questions
            
            # ID 재정렬
            for i, q in enumerate(merged_questions):
                if school_type == "중학교":
                    q['id'] = f"MS{i+1:03d}"
                elif school_type == "고등학교":
                    q['id'] = f"HS{i+1:03d}"
                else:
                    q['id'] = f"SHS{i+1:03d}"
            
            # 저장
            filename = self.get_filename(school_type)
            backup_filename = f"data_files/questions/backup_{timestamp}_{filename.split('/')[-1]}"
            
            # 백업
            if os.path.exists(filename):
                os.makedirs(os.path.dirname(backup_filename), exist_ok=True)
                with open(filename, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                with open(backup_filename, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                print(f"백업 완료: {backup_filename}")
            
            # 새 파일 저장
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(merged_questions, f, ensure_ascii=False, indent=2)
            
            print(f"저장 완료: {filename} ({len(merged_questions)}개)")
    
    def load_existing_questions(self, school_type):
        """기존 문제 로드"""
        filename = self.get_filename(school_type)
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def get_filename(self, school_type):
        """파일명 반환"""
        if school_type == "중학교":
            return "data_files/questions/middle_school_questions.json"
        elif school_type == "고등학교":
            return "data_files/questions/high_school_questions.json"
        else:
            return "data_files/questions/software_high_school_questions.json"
    
    def generate_summary(self, questions_dict):
        """생성 결과 요약"""
        print("\n" + "="*60)
        print("생성 결과 요약")
        print("="*60)
        
        for school_type, questions in questions_dict.items():
            if not questions:
                continue
            
            print(f"\n{school_type}:")
            print(f"  총 문제 수: {len(questions)}개")
            
            # 난이도별 분포
            difficulty_dist = {}
            for q in questions:
                diff = q.get('difficulty', '미지정')
                difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
            
            print("  난이도별 분포:")
            for diff, count in difficulty_dist.items():
                print(f"    {diff}: {count}개 ({count/len(questions)*100:.1f}%)")

# 사용 예시
if __name__ == "__main__":
    print("문제 데이터 확장 도구")
    print("="*60)
    print("주의: OpenAI API 키가 .env 파일에 설정되어 있어야 합니다.")
    print("      API 사용료가 발생할 수 있습니다.")
    print("="*60)
    
    # 사용자 확인
    choice = input("\n진행하시겠습니까? (y/n): ")
    
    if choice.lower() != 'y':
        print("취소되었습니다.")
        exit()
    
    # 목표 설정
    print("\n목표 문제 수 설정:")
    target = input("학교 유형당 목표 문제 수 (기본값: 300): ").strip()
    target = int(target) if target else 300
    
    batch = input("배치 크기 (기본값: 5): ").strip()
    batch = int(batch) if batch else 5
    
    delay = input("API 호출 간격(초) (기본값: 2): ").strip()
    delay = float(delay) if delay else 2
    
    # 실행
    expander = QuestionDataExpander()
    
    print(f"\n생성 시작...")
    print(f"- 학교 유형당 목표: {target}개")
    print(f"- 배치 크기: {batch}개")
    print(f"- 호출 간격: {delay}초")
    print(f"- 예상 소요 시간: 약 {(target * 3 / batch * delay / 60):.1f}분")
    
    confirm = input("\n시작하시겠습니까? (y/n): ")
    
    if confirm.lower() == 'y':
        questions = expander.expand_questions(
            target_per_school=target,
            batch_size=batch,
            delay=delay
        )
        
        expander.generate_summary(questions)
        
        save = input("\n파일로 저장하시겠습니까? (y/n): ")
        if save.lower() == 'y':
            expander.save_questions(questions)
            print("\n완료!")
    else:
        print("취소되었습니다.")
