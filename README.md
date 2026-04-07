# computer-exam-problem

Streamlit 기반 적응형 학습 플랫폼으로, 정보교과 시험 문제를 자동 생성하고 학습자/교사 피드백을 수집합니다. 학생은 개인화된 문제 세트를 받아 실시간으로 풀이하고, 교사는 동일한 데이터 소스로 문제 품질을 검토하며 피드백을 남깁니다.

## Architecture
![exam-system](image/Exam_System.png)

위 다이어그램은 이 프로젝트의 목표 아키텍처를 보여줍니다. 현재 저장소 기준으로는 Streamlit UI, 문제 생성 API 래퍼, 피드백 CSV 저장, 교사용 검토 화면, GNN 프로토타입이 구현되어 있으며, `Supabase`/`PostgreSQL` 중심 저장소와 별도 서비스형 `api wrapper`는 설계 방향에 가깝습니다.

## Architecture Flow
1. **학생 인터페이스**: `app.py` 기반 Streamlit 화면에서 학생이 학번, 학교 유형, 난이도, 문제 수를 선택하고 문제 생성을 요청합니다.
2. **문제 생성 요청**: 학생 요청은 `api.py`의 생성 래퍼로 전달되며, 학교급/난이도/단원 조건을 포함한 프롬프트를 구성합니다.
3. **참고 문제 활용**: `data_files/questions/*.json`의 기존 문항 세트를 few-shot 참고 데이터로 삼아 문제 형식과 난이도 일관성을 유지합니다.
4. **LLM 생성 계층**: 현재 구현은 `OpenAI` 또는 `Gemini` 백엔드를 사용하며, 다이어그램에서는 `gpt-4o-mini` 기반 생성 계층으로 표현되어 있습니다.
5. **학생 풀이 및 피드백 수집**: 생성된 문제는 학생 화면에 제시되고, 답안 및 난이도 체감/의견은 `data_files/feedback/feedback.csv`에 저장됩니다.
6. **교사 검토 인터페이스**: `teacher_feedback.py`에서 생성 문제 검토, 학생 피드백 분석, 수정 요청 처리를 수행합니다.
7. **재학습 및 분석 루프**: 누적 피드백은 `gnn_model.py`의 난이도 추정 실험이나 추가 분석용 CSV 입력으로 사용됩니다. 다이어그램의 `Fetch Feedback Retraining`과 `GNN`은 이 루프를 확장한 목표 상태를 의미합니다.

## Implementation Status
| 영역 | 다이어그램 상 역할 | 현재 저장소 상태 |
| --- | --- | --- |
| Streamlit Student Interface | 학생 문제 생성/풀이 UI | 구현됨 (`app.py`) |
| Streamlit Teacher Interface | 교사 검토/통계 UI | 구현됨 (`teacher_feedback.py`) |
| API Wrapper | LLM 호출 및 문제 생성 | 구현됨 (`api.py`) |
| Real Reference Questions | 참고 문제 뱅크 | 구현됨 (`data_files/questions/*.json`) |
| Few-Shot Prompt | 생성 품질 보강 | 부분 구현됨. 현재는 프롬프트 기반 생성 중심 |
| Feedback CSV | 학생/교사 피드백 저장 | 구현됨 (`data_files/feedback/`) |
| GNN | 난이도 예측/재학습 | 프로토타입 구현 (`gnn_model.py`) |
| Supabase / PostgreSQL | 중앙 저장소 | 다이어그램 기준 설계 요소, 현재 기본 저장은 CSV |
| 별도 모델 서비스 API | 외부 추론 서비스 | 다이어그램 기준 설계 요소 |

## Key Capabilities
- **학생**: 난이도·학교 유형에 맞춘 문제 생성, 단계형 응시 플로우, 즉시 채점과 피드백 제출
- **교사**: 문제 세트 재검토, 품질/난이도 평가, 수정 요청 워크플로, 학생 피드백 통계 확인
- **AI/ML**: LLM 기반 문제 생성 래퍼, GNN 난이도 추정기(`gnn_model.py`) 프로토타입, 데이터 증강/시뮬레이션 스크립트
- **데이터 계층**: 기본 문제 JSON, 실행 중 생성되는 피드백 CSV, Redis 캐시 기반 문제 생성 최적화

## Repository Layout
```text
computer-exam-problem/
├── app.py                  # 학생용 Streamlit 엔트리 포인트
├── teacher_feedback.py     # 교사용 Streamlit 엔트리 포인트
├── api.py                  # OpenAI 문제 생성 래퍼
├── cache.py                # Redis 기반 문제 캐시 / 요청 코얼레싱
├── gnn_model.py            # GNN 난이도 예측기
├── augment_questions.py    # 기존 문제 증강 도구
├── expand_questions.py     # 신규 문제 확장 스크립트
├── generate_feedback.py    # 시뮬레이션 기반 피드백 생성기
├── dummy_data_gen.py       # 더미 데이터 생성 스크립트
├── data_files/
│   ├── questions/          # 트래킹되는 기본 문제 JSON
│   └── feedback/           # 런타임 CSV 저장소 (Git 무시)
├── requirements.txt        # 런타임 의존성
├── requirements-dev.txt    # 개발/실험 의존성
├── .env.example            # 환경변수 템플릿
├── DATA_AUGMENTATION_GUIDE.md
├── CLEANUP_SUMMARY.md
└── 2025-11-08-project-cleanup.md
```

## Getting Started
1. **Python 환경**: Python 3.12 권장. 가상환경 생성 후 활성화합니다.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. **의존성 설치**:
   ```bash
   pip install -r requirements.txt
   ```
3. **환경변수**: `.env.example`를 복사하여 `.env`를 만들고 OpenAI API 키 등 필드를 채웁니다.
4. **앱 실행**:
   ```bash
   streamlit run app.py                # 학생용 인터페이스
   streamlit run teacher_feedback.py   # 교사용 인터페이스
   ```

## Environment Variables
| 변수 | 설명 | 기본값 |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI 백엔드 사용 시 필요 | 없음 |
| `GEMINI_API_KEY` | Gemini 백엔드 사용 시 필요 | 없음 |
| `AI_BACKEND` | 문제 생성 백엔드 선택 (`openai`, `gemini`) | `gemini` |
| `REDIS_URL` | Redis 캐시 서버 주소 | `redis://localhost:6379/0` |
| `LOG_LEVEL` | 애플리케이션 로그 레벨 | `INFO` |
| `LOG_FILE` | 로그 파일 경로 | `logs/app.log` |
| `DEBUG` | `True` 시 디버그 모드 | `False` |
| `TEACHER_PASSWORD` | 교사용 뷰 간단 패스워드 | `teacher2025` |

## Data Management
- `data_files/questions/*.json`: 레포에 포함된 기본 문제 세트입니다. 필요 시 `augment_questions.py`나 `expand_questions.py`로 새 변형을 생성할 수 있습니다.
- `data_files/feedback/`: `app.py`와 `teacher_feedback.py` 실행 중 생성되는 `feedback.csv`, `teacher_feedback.csv`를 저장합니다. Git에서 제외되며, 실행 시 자동으로 만들어집니다. 디렉토리 설명은 `data_files/feedback/README.md`를 참고하세요.
- 다이어그램의 `Supabase`/`PostgreSQL`은 장기적으로 옮겨갈 중앙 저장소 구조를 의미합니다. 현재 기본 동작은 로컬 JSON + CSV 파일 저장입니다.

## Optional Services
- `docker-compose.yml`에는 문제 생성 캐시와 요청 코얼레싱을 위한 Redis 서비스가 포함되어 있습니다.
- Redis를 사용하려면 다음 명령으로 실행합니다.
  ```bash
  docker compose up -d
  ```
- Redis가 없어도 앱은 동작하지만, 중복 생성 요청 최적화와 캐시 이점은 비활성화됩니다.

## Utility Scripts
- `augment_questions.py`: 동의어 치환, 숫자 변형, 보기 셔플 등으로 기존 문제를 증강합니다.
- `expand_questions.py`: 주어진 단원/난이도 조합별 문제 템플릿을 확장할 때 사용합니다.
- `generate_feedback.py`: 현실적인 학생/교사 반응을 시뮬레이션해 GNN 학습용 피드백 CSV를 생성합니다.
- `dummy_data_gen.py`: 빠른 UI 테스트용 샘플 데이터를 만듭니다.

## GNN Difficulty Model
`gnn_model.py`는 `DifficultyPredictor` 클래스를 제공하며, 텍스트 기반 특징을 이용해 난이도를 예측합니다.
```python
from gnn_model import DifficultyPredictor

predictor = DifficultyPredictor()
predictor.train_model(
    'data_files/questions/middle_school_questions.json',
    'data_files/feedback/feedback.csv'
)
predictor.save_model('models_saved/difficulty_model.pth')
```
- 학습 데이터는 JSON 문제 세트와 선택적 피드백 CSV에서 생성됩니다.
- Streamlit 앱에서는 아직 실시간 학습을 실험 중이며, 기본값으로 `중` 난이도를 반환합니다.

## Status & Roadmap
- [완료] Streamlit UI 리팩터링, 데이터 경로 통일 (`data_files/*`)
- [완료] 피드백 저장/로깅, 기본 GNN 파이프라인 초안
- [진행중] GNN 실서비스 통합, 적응형 추천 로직 고도화
- [진행중] 추가 학교 유형/다중 사용자 세션 관리
- [진행중] API 서비스화 및 배포 자동화

## Troubleshooting
- **OpenAI 인증 오류**: `.env`에 `OPENAI_API_KEY`가 존재하는지 확인 후 `source .env` 또는 Streamlit 재실행
- **데이터 파일 없음**: `data_files/questions/` 구조가 없으면 `mkdir -p data_files/questions` 후 JSON을 배치
- **의존성 문제**: `pip install -r requirements.txt --upgrade`로 재설치

## Contributing
1. 이슈 등록으로 변경 사항 논의
2. 기능 브랜치 생성 후 커밋
3. PR에 테스트/실행 방법을 첨부합니다.

## License / Usage
본 프로젝트는 교육 목적으로 제작되었습니다. 내부 실험이나 수업용으로 자유롭게 사용하되, 민감한 학생 데이터는 레포에 포함하지 마십시오.
