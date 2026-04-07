"""문제 증강 도구: 기존 문항을 동의어, 숫자 조정, 선택지 셔플로 다양화."""

import json
import random
import re
from copy import deepcopy

class QuestionAugmenter:
    """문제 증강 클래스"""
    
    def __init__(self):
        # 동의어 사전 (UI 용어와 교육 용어를 모두 포함)
        self.synonyms = {
            "변수": ["변수", "변인", "매개변수"],
            "함수": ["함수", "메서드", "프로시저"],
            "반복문": ["반복문", "루프", "순환문"],
            "조건문": ["조건문", "분기문", "선택문"],
            "배열": ["배열", "어레이", "리스트"],
            "알고리즘": ["알고리즘", "해법", "풀이법"],
            "프로그래밍": ["프로그래밍", "코딩", "프로그램 작성"],
            "데이터": ["데이터", "자료", "정보"],
            "입력": ["입력", "인풋", "입력값"],
            "출력": ["출력", "아웃풋", "출력값"],
            "저장": ["저장", "보관", "기록"],
            "실행": ["실행", "구동", "작동"],
            "선언": ["선언", "정의", "지정"],
            "사용": ["사용", "이용", "활용"],
        }
        
        # 숫자 변경 범위
        self.number_range = (-5, 5)  # -5 ~ +5 범위로 변경
    
    def augment_question(self, question, num_variations=3):
        """하나의 문제로부터 여러 변형 생성"""
        variations = []
        
        for i in range(num_variations):
            variation = deepcopy(question)
            
            # 증강 기법 랜덤 선택 (여러 개 동시 적용 가능)
            techniques = []
            
            if random.random() > 0.5:
                techniques.append('synonym')
            if random.random() > 0.5:
                techniques.append('number')
            if random.random() > 0.7:
                techniques.append('shuffle_options')
            
            # 최소 하나는 적용
            if not techniques:
                techniques.append(random.choice(['synonym', 'number', 'shuffle_options']))
            
            # 각 기법 적용
            for technique in techniques:
                if technique == 'synonym':
                    variation = self.replace_synonyms(variation)
                elif technique == 'number':
                    variation = self.modify_numbers(variation)
                elif technique == 'shuffle_options':
                    variation = self.shuffle_options(variation)
            
            # ID 수정
            original_id = question.get('id', 'Q000')
            variation['id'] = f"{original_id}_aug{i+1}"
            
            # 메타데이터 추가
            variation['augmented'] = True
            variation['original_id'] = original_id
            variation['augmentation_techniques'] = techniques
            
            variations.append(variation)
        
        return variations
    
    def replace_synonyms(self, question):
        """동의어 치환"""
        q_text = question.get('question', '')
        
        for word, synonyms in self.synonyms.items():
            if word in q_text:
                # 원래 단어 제외하고 랜덤 선택
                available_synonyms = [s for s in synonyms if s != word]
                if available_synonyms:
                    new_word = random.choice(available_synonyms)
                    q_text = q_text.replace(word, new_word)
        
        question['question'] = q_text
        
        # 선택지도 같은 방식으로 처리
        if 'options' in question:
            new_options = []
            for opt in question['options']:
                for word, synonyms in self.synonyms.items():
                    if word in opt:
                        available_synonyms = [s for s in synonyms if s != word]
                        if available_synonyms:
                            new_word = random.choice(available_synonyms)
                            opt = opt.replace(word, new_word)
                new_options.append(opt)
            question['options'] = new_options
        
        return question
    
    def modify_numbers(self, question):
        """숫자 값 변경"""
        q_text = question.get('question', '')
        
        # 숫자 찾기 및 변경
        def replace_number(match):
            num = int(match.group())
            # 작은 숫자는 변경 폭 작게
            if abs(num) < 10:
                delta = random.randint(-2, 2)
            else:
                delta = random.randint(*self.number_range)
            
            new_num = num + delta
            # 0 이하가 되지 않도록
            if new_num <= 0 and num > 0:
                new_num = num
            
            return str(new_num)
        
        q_text = re.sub(r'\b\d+\b', replace_number, q_text)
        question['question'] = q_text
        
        return question
    
    def shuffle_options(self, question):
        """선택지 순서 섞기 (정답도 함께 업데이트)"""
        if 'options' not in question or 'answer' not in question:
            return question
        
        options = question['options']
        
        # 현재 정답 찾기
        try:
            answer_idx = int(question['answer']) - 1
            correct_answer = options[answer_idx]
        except:
            # answer가 텍스트인 경우
            correct_answer = question['answer']
        
        # 선택지 섞기
        random.shuffle(options)
        question['options'] = options
        
        # 새로운 정답 위치 찾기
        try:
            new_answer_idx = options.index(correct_answer)
            question['answer'] = str(new_answer_idx + 1)
        except ValueError:
            pass  # 정답을 찾지 못하면 그대로 유지
        
        return question
    
    def augment_dataset(self, questions, variations_per_question=2):
        """전체 데이터셋 증강"""
        augmented = []
        
        print(f"데이터 증강 시작: {len(questions)}개 문제")
        print(f"문제당 {variations_per_question}개 변형 생성")
        
        for idx, question in enumerate(questions):
            if (idx + 1) % 10 == 0:
                print(f"진행중... {idx + 1}/{len(questions)}")
            
            variations = self.augment_question(question, variations_per_question)
            augmented.extend(variations)
        
        print(f"증강 완료: {len(augmented)}개 생성")
        return augmented
    
    def save_augmented_data(self, original_file, augmented_questions):
        """증강된 데이터 저장"""
        # 원본 데이터 로드
        with open(original_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # 병합
        merged_data = original_data + augmented_questions
        
        # 백업 파일명
        backup_file = original_file.replace('.json', '_backup.json')
        
        # 원본 백업
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
        print(f"원본 백업: {backup_file}")
        
        # 새 파일 저장
        output_file = original_file.replace('.json', '_augmented.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        print(f"증강 데이터 저장: {output_file}")
        
        return output_file

# 사용 예시
if __name__ == "__main__":
    import os
    
    print("문제 데이터 증강 도구")
    print("="*60)
    print("기존 문제를 변형하여 새로운 학습 데이터를 생성합니다.")
    print("="*60)
    
    # 파일 선택
    files = {
        '1': 'data_files/questions/middle_school_questions.json',
        '2': 'data_files/questions/software_high_school_questions.json',
        '3': '모두'
    }
    
    print("\n증강할 파일 선택:")
    for key, file in files.items():
        print(f"{key}. {file}")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    if choice not in files:
        print("잘못된 선택입니다.")
        exit()
    
    variations = input("문제당 생성할 변형 개수 (기본값: 2): ").strip()
    variations = int(variations) if variations else 2
    
    augmenter = QuestionAugmenter()
    
    if choice == '3':
        # 모든 파일 처리
        for key in ['1', '2']:
            file_path = files[key]
            if os.path.exists(file_path):
                print(f"\n처리중: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                augmented = augmenter.augment_dataset(questions, variations)
                augmenter.save_augmented_data(file_path, augmented)
    else:
        # 선택된 파일만 처리
        file_path = files[choice]
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            augmented = augmenter.augment_dataset(questions, variations)
            augmenter.save_augmented_data(file_path, augmented)
        else:
            print(f"파일을 찾을 수 없습니다: {file_path}")
    
    print("\n완료!")
