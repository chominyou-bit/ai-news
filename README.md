# ⚡ AI 뉴스 TOP 5

RSS 피드 자동 수집 + 한국어 번역 카드뉴스 웹앱  
**API 키 불필요 · GitHub Pages 무료 배포 · 매일 자동 업데이트**

---

## 🚀 GitHub Pages 배포 (온라인 공개)

### 1단계 — GitHub 저장소 만들기

[github.com/new](https://github.com/new) 에서 새 저장소 생성  
- Repository name: `ai-news` (원하는 이름)
- Public 선택
- **Initialize this repository 체크 해제**

### 2단계 — 코드 올리기

터미널에서 아래 명령어 순서대로 실행:

```bash
cd ~/클로드\ 연습/ai-news

git init
git add .
git commit -m "🚀 첫 배포"
git branch -M main
git remote add origin https://github.com/내아이디/ai-news.git
git push -u origin main
```

### 3단계 — GitHub Pages 활성화

1. GitHub 저장소 → **Settings** 탭
2. 왼쪽 메뉴 **Pages** 클릭
3. Source: **Deploy from a branch**
4. Branch: **main** / **/ (root)** 선택 → **Save**
5. 잠시 후 `https://내아이디.github.io/ai-news/` 접속 가능

### 4단계 — 완료!

- 매일 **오전 9시** 자동으로 뉴스 수집 + 번역 + 배포
- GitHub Actions 탭에서 실행 상태 확인 가능
- **수동 실행**: Actions → "AI 뉴스 자동 업데이트" → Run workflow

---

## 💻 로컬 실행

```bash
# 뉴스 수집 (인터넷 필요)
python3 fetch_news.py

# 웹서버
cd ~/클로드\ 연습
python3 -m http.server 8080
# → http://localhost:8080/ai-news/
```

---

## 📁 파일 구조

```
ai-news/
├── .github/
│   └── workflows/
│       └── update-news.yml   ← GitHub Actions (매일 자동 실행)
├── index.html                ← 웹 UI
├── style.css                 ← 디자인
├── news.json                 ← 뉴스 데이터 (자동 업데이트)
├── fetch_news.py             ← RSS 수집 + 번역 스크립트
└── README.md
```

---

## 📡 뉴스 출처

| 매체 | 분야 |
|------|------|
| VentureBeat | AI 전문 |
| TechCrunch | AI 카테고리 |
| The Verge | 테크 전반 |
| Ars Technica | 기술 심층 |
| WIRED | AI 태그 |
