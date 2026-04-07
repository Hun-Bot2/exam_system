"""UI 테스트 및 모델 학습용 더미 데이터 생성기."""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import json
import uuid

class DummyDataGenerator:
    def __init__(self):
        # 중학교 1학년, 고등학교 1학년 학생 프로필
        self.student_profiles = {
            'middle_school': {
                'grade': '중학교 1학년',
                'programming_experience': 'low',  # 낮은 프로그래밍 경험
                'difficulty_preference': ['하', '중'],  # 선호 난이도
                'accuracy_range': (0.3, 0.7),  # 정답률 범위
                'difficulty_rating_bias': -0.5  # 난이도를 더 어렵게 느끼는 경향
            },
            'high_school': {
                'grade': '고등학교 1학년', 
                'programming_experience': 'medium',  # 중간 프로그래밍 경험
                'difficulty_preference': ['중', '상'],
                'accuracy_range': (0.5, 0.8),
                'difficulty_rating_bias': 0  # 중립적
            }
        }
        
        # 학생 성향 타입
        self.student_types = {
            'high_performer': {'accuracy_bonus': 0.2, 'confidence': 'high'},
            'average_performer': {'accuracy_bonus': 0, 'confidence': 'medium'},
            'low_performer': {'accuracy_bonus': -0.2, 'confidence': 'low'},
            'inconsistent': {'accuracy_bonus': 0, 'confidence': 'variable'}
        }
        
        # 단원별 학생 선호도/능력
        self.unit_preferences = {
            '알고리즘': {'difficulty_multiplier': 1.2, 'interest': 'high'},
            '프로그래밍': {'difficulty_multiplier': 1.1, 'interest': 'high'},
            '자료구조': {'difficulty_multiplier': 1.3, 'interest': 'medium'},
            '네트워크': {'difficulty_multiplier': 0.9, 'interest': 'low'},
            '데이터베이스': {'difficulty_multiplier': 0.8, 'interest': 'low'},
            '정보사회': {'difficulty_multiplier': 0.7, 'interest': 'medium'}
        }
    
    def generate_student_list(self, num_middle=30, num_high=30):
        """학생 리스트 생성"""
        students = []
        
        # 중학교 1학년 학생들
        for i in range(num_middle):
            student_type = random.choice(list(self.student_types.keys()))
            students.append({
                'student_id': f'M2025{i+1:03d}',
                'grade': '중학교 1학년',
                'profile_type': 'middle_school',
                'student_type': student_type,
                'name': f'중학생{i+1}',
                'programming_experience': random.choice(['none', 'basic', 'some']),
                'base_accuracy': random.uniform(*self.student_profiles['middle_school']['accuracy_range'])
            })
        
        # 고등
