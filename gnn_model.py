"""Prototype Graph Neural Network for estimating question difficulty."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data, DataLoader
import numpy as np
import pandas as pd
import json
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pickle
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DifficultyGNN(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, output_dim=3):
        super(DifficultyGNN, self).__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, hidden_dim//2)
        self.classifier = nn.Linear(hidden_dim//2, output_dim)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x, edge_index, batch):
        x = F.relu(self.conv1(x, edge_index))
        x = self.dropout(x)
        x = F.relu(self.conv2(x, edge_index))
        x = self.dropout(x)
        x = F.relu(self.conv3(x, edge_index))
        
        # Graph-level representation
        x = global_mean_pool(x, batch)
        x = self.classifier(x)
        return F.log_softmax(x, dim=1)

class QuestionFeatureExtractor:
    def __init__(self):
        self.tfidf = TfidfVectorizer(max_features=100, stop_words=None)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.programming_keywords = [
            '알고리즘', '프로그래밍', '변수', '함수', '반복문', '조건문', 
            'for', 'while', 'if', 'else', '배열', '리스트', '정렬', '탐색',
            'python', 'java', 'c++', '코딩', '디버깅', '자료구조'
        ]
        
    def extract_features(self, questions_data):
        """문제 데이터에서 feature 추출"""
        features = []
        
        for question in questions_data:
            # 1. 텍스트 기반 features
            question_text = question.get('question', '')
            text_length = len(question_text)
            word_count = len(question_text.split())
            
            # 2. 프로그래밍 키워드 개수
            programming_score = sum(1 for keyword in self.programming_keywords 
                                  if keyword.lower() in question_text.lower())
            
            # 3. 선택지 복잡도
            choices = question.get('choices', [])
            avg_choice_length = np.mean([len(choice) for choice in choices]) if choices else 0
            
            # 4. 단원별 가중치
            unit = question.get('unit', '')
            unit_difficulty = self.get_unit_difficulty(unit)
            
            # 5. 수식 및 코드 포함 여부
            has_code = bool(re.search(r'[(){}\[\]]|def |for |if |while ', question_text))
            has_math = bool(re.search(r'[+\-*/=<>]|\d+', question_text))
            
            feature_vector = [
                text_length, word_count, programming_score, avg_choice_length,
                unit_difficulty, int(has_code), int(has_math)
            ]
            
            features.append(feature_vector)
            
        return np.array(features)
    
    def get_unit_difficulty(self, unit):
        """단원별 기본 난이도 가중치"""
        difficulty_map = {
            '알고리즘': 3, '프로그래밍': 3, '자료구조': 3,
            '네트워크': 2, '데이터베이스': 2, '소프트웨어': 2,
            '정보사회': 1, '컴퓨터구조': 2, '운영체제': 2
        }
        return difficulty_map.get(unit, 1)
    
    def create_graph_data(self, features, labels=None, similarity_threshold=0.7):
        """문제 간 유사도를 기반으로 그래프 데이터 생성"""
        num_questions = len(features)
        
        # 코사인 유사도 계산
        from sklearn.metrics.pairwise import cosine_similarity
        similarity_matrix = cosine_similarity(features)
        
        # 엣지 생성 (유사도가 threshold 이상인 문제들 연결)
        edge_index = []
        for i in range(num_questions):
            for j in range(i+1, num_questions):
                if similarity_matrix[i][j] > similarity_threshold:
                    edge_index.append([i, j])
                    edge_index.append([j, i])  # 무방향 그래프
        
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        x = torch.tensor(features, dtype=torch.float)
        
        if labels is not None:
            y = torch.tensor(labels, dtype=torch.long)
            return Data(x=x, edge_index=edge_index, y=y)
        else:
            return Data(x=x, edge_index=edge_index)

class DifficultyPredictor:
    def __init__(self):
        self.model = None
        self.feature_extractor = QuestionFeatureExtractor()
        self.is_trained = False
        
    def prepare_training_data(self, questions_file, feedback_file=None):
        """훈련 데이터 준비"""
        try:
            # JSON 파일에서 문제 데이터 로드
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
            
            # Feature 추출
            features = self.feature_extractor.extract_features(questions_data)
            
            # 난이도 레이블 (하=0, 중=1, 상=2)
            difficulty_map = {'하': 0, '중': 1, '상': 2}
            labels = [difficulty_map.get(q.get('difficulty', '중'), 1) for q in questions_data]
            
            # 피드백 데이터가 있다면 추가 정보 활용
            if feedback_file and os.path.exists(feedback_file):
                try:
                    feedback_df = pd.read_csv(feedback_file)
                    # 문제별 평균 난이도 평가 반영
                    for i, question in enumerate(questions_data):
                        question_feedback = feedback_df[
                            feedback_df['question_id'] == question.get('id', i+1)
                        ]
                        if not question_feedback.empty:
                            avg_rating = question_feedback['difficulty_rating'].mean()
                            # 피드백 기반 난이도 조정
                            if avg_rating <= 2:
                                labels[i] = 0  # 하
                            elif avg_rating <= 3.5:
                                labels[i] = 1  # 중
                            else:
                                labels[i] = 2  # 상
                except Exception as e:
                    logger.warning(f"피드백 데이터 처리 중 오류 발생: {str(e)}")
            
            return features, labels, questions_data
        except Exception as e:
            logger.error(f"훈련 데이터 준비 중 오류 발생: {str(e)}")
            raise
    
    def train_model(self, questions_file, feedback_file=None):
        """GNN 모델 훈련"""
        features, labels, _ = self.prepare_training_data(questions_file, feedback_file)
        
        # Feature 정규화
        features = self.feature_extractor.scaler.fit_transform(features)
        
        # 그래프 데이터 생성
        graph_data = self.feature_extractor.create_graph_data(features, labels)
        
        # 모델 초기화
        input_dim = features.shape[1]
        self.model = DifficultyGNN(input_dim)
        
        # 훈련
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        criterion = nn.NLLLoss()
        
        self.model.train()
        for epoch in range(200):
            optimizer.zero_grad()
            batch = torch.zeros(graph_data.x.size(0), dtype=torch.long)
            out = self.model(graph_data.x, graph_data.edge_index, batch)
            loss = criterion(out, graph_data.y)
            loss.backward()
            optimizer.step()
            
            if epoch % 50 == 0:
                print(f'Epoch {epoch}, Loss: {loss.item():.4f}')
        
        self.is_trained = True
        print("모델 훈련 완료!")
    
    def update_training_data(self, features: dict, difficulty_rating: int) -> None:
        """학생 피드백을 수집해 향후 재훈련에 활용한다 (현재는 데이터 누적만)."""
        # 실시간 온라인 학습은 미구현 — 피드백 CSV에 이미 저장되므로 여기선 pass
        pass

    def predict_difficulty(self, question_text, choices=None, unit=''):
        """새로운 문제의 난이도 예측"""
        if not self.is_trained:
            return '중'  # 기본값
        
        # 문제 데이터 구성
        question_data = [{
            'question': question_text,
            'choices': choices or [],
            'unit': unit
        }]
        
        # Feature 추출
        features = self.feature_extractor.extract_features(question_data)
        features = self.feature_extractor.scaler.transform(features)
        
        # 그래프 데이터 생성 (단일 노드)
        graph_data = self.feature_extractor.create_graph_data(features)
        
        # 예측
        self.model.eval()
        with torch.no_grad():
            batch = torch.zeros(1, dtype=torch.long)
            out = self.model(graph_data.x, graph_data.edge_index, batch)
            predicted = torch.argmax(out, dim=1).item()
        
        difficulty_map = {0: '하', 1: '중', 2: '상'}
        return difficulty_map[predicted]
    
    def save_model(self, filepath):
        """모델 저장"""
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # CUDA 사용 가능 여부 확인
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            # 모델을 CPU로 이동하여 저장
            self.model.to('cpu')
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'feature_extractor': self.feature_extractor,
                'is_trained': self.is_trained
            }, filepath)
            
            # 원래 디바이스로 복원
            self.model.to(device)
            logger.info(f"모델이 성공적으로 저장되었습니다: {filepath}")
        except Exception as e:
            logger.error(f"모델 저장 중 오류 발생: {str(e)}")
            raise
    
    def load_model(self, filepath):
        """모델 로드"""
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {filepath}")
            
            # CUDA 사용 가능 여부 확인
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            checkpoint = torch.load(filepath, map_location=device)
            input_dim = 7  # feature 개수
            self.model = DifficultyGNN(input_dim)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.feature_extractor = checkpoint['feature_extractor']
            self.is_trained = checkpoint['is_trained']
            
            # 모델을 적절한 디바이스로 이동
            self.model.to(device)
            logger.info(f"모델이 성공적으로 로드되었습니다: {filepath}")
        except Exception as e:
            logger.error(f"모델 로드 중 오류 발생: {str(e)}")
            raise

# 사용 예시
if __name__ == "__main__":
    predictor = DifficultyPredictor()
    
    # 기존 데이터로 모델 훈련
    predictor.train_model(
        'data_files/questions/middle_school_questions.json',
        'data_files/feedback/feedback.csv'
    )
    
    # 새로운 문제 난이도 예측
    new_question = "다음 파이썬 코드의 출력 결과는?"
    predicted_difficulty = predictor.predict_difficulty(new_question, unit='프로그래밍')
    print(f"예측된 난이도: {predicted_difficulty}")
    
    # 모델 저장
    predictor.save_model('difficulty_model.pth')
