# Commit & Test Order

## 1. Environment Setup (first time only)

```bash
# Copy env file and fill in your OpenAI API key
cp .env.example .env

# Install runtime dependencies
pip install -r requirements.txt

# Install dev/test dependencies
pip install -r requirements-dev.txt
```

Required `.env` values:
```
OPENAI_API_KEY=sk-...
TEACHER_PASSWORD=your_password_here
```

---

## 2. Running the Program

### Student app
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`

### Teacher dashboard (separate terminal)
```bash
streamlit run teacher_feedback.py
```
Opens at `http://localhost:8502`

> Run both simultaneously with different ports if needed:
> ```bash
> streamlit run teacher_feedback.py --server.port 8502
> ```

---

## 3. Manual Test Checklist

Run through these after every significant change.

### Student Flow (`app.py`)
- [ ] Login: enter any student ID → click next
- [ ] Setup: pick difficulty / question count / school type → click generate
- [ ] Generate: questions appear with predicted difficulty bar chart
- [ ] Solve: answer all questions, navigate prev/next, click finish
- [ ] Feedback: rate each question 1–5, submit all
- [ ] Complete: score shows correctly, restart button works
- [ ] Check `data_files/feedback/feedback.csv` was created/updated

### Teacher Flow (`teacher_feedback.py`)
- [ ] Login fails with wrong password, succeeds with correct one
- [ ] Menu: 문제 생성 및 검토 → generate questions → approve / request modification
- [ ] Menu: 학생 피드백 분석 → loads feedback.csv stats (run student flow first)
- [ ] Menu: 문제 수정 요청 → shows flagged questions from teacher_feedback.csv
- [ ] Menu: 통계 대시보드 → pie, bar, and line charts render

### API wrapper (`api.py`)
- [ ] Valid OPENAI_API_KEY returns a list of questions
- [ ] Missing API key shows a clean error message (not a stack trace)
- [ ] Retry: disconnect network mid-run → spinner shows retry count, returns `[]` after 3 attempts

---

## 4. Lint & Format Before Committing

```bash
# Auto-format
black app.py teacher_feedback.py api.py gnn_model.py

# Check style
flake8 app.py teacher_feedback.py api.py gnn_model.py

# Type check (optional)
mypy app.py api.py gnn_model.py
```

Fix any errors before moving to the commit step.

---

## 5. Commit Convention

Format: `<type>: <short summary in English, lowercase>`

| Type | When to use |
|------|-------------|
| `feat` | New feature or screen |
| `fix` | Bug fix |
| `refactor` | Code restructure, no behavior change |
| `style` | Formatting only (black/flake8) |
| `docs` | README, comments, markdown files |
| `data` | Changes to JSON question banks or CSV seeds |
| `chore` | Dependency updates, config, .env changes |

### Examples
```
feat: add general high school question bank
fix: normalize answer format to string in api.py
refactor: split teacher dashboard into separate modules
docs: update README setup instructions
data: expand middle school questions to 200 items
chore: upgrade openai sdk to 1.20.0
```

### Commit Steps
```bash
# 1. Stage only the files you changed
git add app.py api.py

# 2. Commit with a message following the convention above
git commit -m "fix: add retry logic to api and normalize answer format"

# 3. Push when ready
git push origin main
```

> Never use `git add .` blindly — it can accidentally stage `.env` or large data files.

---

## 6. Offline Data Utilities (run when needed, not on every commit)

```bash
# Expand question bank (calls OpenAI — costs tokens)
python expand_questions.py

# Augment existing questions with variations (no API call)
python augment_questions.py

# Generate simulated student feedback for testing
python generate_feedback.py
```

---

## 7. GNN Model Training (optional)

Only needed when rebuilding the difficulty predictor from scratch:

```bash
python gnn_model.py
# Trains on data_files/questions/middle_school_questions.json
# Saves model to difficulty_model.pth
```

The trained model is loaded automatically by `app.py` at startup via `@st.cache_resource`.
