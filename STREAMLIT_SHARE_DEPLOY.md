# Streamlit Share 배포 가이드 (OpenAI 챗봇)

## 1) 실행 파일
- 배포할 앱 파일: `chatbot_app.py`

## 2) 필수 패키지
- `requirements.txt`에 `openai`가 포함되어 있어야 함

## 3) Secrets 설정 (중요)
Streamlit Cloud의 앱 설정에서 아래를 넣으세요:

```toml
OPENAI_API_KEY = "sk-..."
```

- 로컬에서는 `.streamlit/secrets.toml` 파일을 직접 만들고 같은 형식으로 넣으면 됩니다.
- `.streamlit/secrets.toml.example` 파일은 템플릿입니다.

## 4) 배포 절차
1. GitHub에 코드 push
2. Streamlit Cloud에서 New app 생성
3. Repository 선택
4. Main file path: `chatbot_app.py`
5. Advanced settings > Secrets에 `OPENAI_API_KEY` 추가
6. Deploy

## 5) 로컬 테스트
```bash
streamlit run chatbot_app.py
```
