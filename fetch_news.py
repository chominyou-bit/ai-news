#!/usr/bin/env python3
"""
AI/테크 뉴스 TOP5 수집기
RSS 피드에서 뉴스 수집 → 한국어 번역 → news.json + 인스타 카드 이미지 생성
사용법: python3 fetch_news.py
"""

import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
RSS_FEEDS = [
    {"url": "https://venturebeat.com/category/ai/feed/",                      "source": "VentureBeat"},
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/",  "source": "TechCrunch"},
    {"url": "https://www.theverge.com/rss/index.xml",                         "source": "The Verge"},
    {"url": "https://feeds.arstechnica.com/arstechnica/technology-lab",       "source": "Ars Technica"},
    {"url": "https://www.wired.com/feed/tag/ai/rss",                          "source": "WIRED"},
]

TAG_RULES = {
    "AI":      ["artificial intelligence", " ai ", "machine learning", "neural", "deep learning"],
    "LLM":     ["gpt", "claude", "gemini", "llama", "language model", "chatgpt", "openai", "anthropic"],
    "로보틱스": ["robot", "robotics", "humanoid", "autonomous"],
    "반도체":   ["chip", "semiconductor", "nvidia", "gpu", "tpu", "npu"],
    "빅테크":   ["google", "microsoft", "apple", "amazon", "meta", "tesla"],
    "스타트업": ["startup", "funding", "raises", "series", "venture"],
    "오픈소스": ["open source", "open-source", "github", "hugging face"],
    "보안":    ["security", "privacy", "hack", "vulnerability", "breach"],
    "규제":    ["regulation", "law", "policy", "ban", "eu", "congress"],
    "연구":    ["research", "paper", "study", "benchmark", "dataset"],
}

# 순위별 포인트 컬러
RANK_COLORS = {
    1: "#e53e3e",  # 빨강
    2: "#38a169",  # 초록
    3: "#805ad5",  # 보라
    4: "#718096",  # 회색
    5: "#3182ce",  # 파랑
}

# ─────────────────────────────────────────
# 폰트 준비
# ─────────────────────────────────────────
FONT_DIR = os.path.join(SCRIPT_DIR, "fonts")
FONT_FILES = {
    "regular": "NanumGothic-Regular.ttf",
    "bold":    "NanumGothic-Bold.ttf",
    "black":   "NanumGothic-ExtraBold.ttf",
}
FONT_URLS = {
    "regular": "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
    "bold":    "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Bold.ttf",
    "black":   "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-ExtraBold.ttf",
}

def ensure_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    for key, fname in FONT_FILES.items():
        path = os.path.join(FONT_DIR, fname)
        if not os.path.exists(path):
            print(f"  폰트 다운로드 중: {fname} ...", end=" ", flush=True)
            try:
                req = urllib.request.Request(
                    FONT_URLS[key],
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    with open(path, "wb") as f:
                        f.write(resp.read())
                print("완료")
            except Exception as e:
                print(f"실패 ({e})")
    return {
        key: os.path.join(FONT_DIR, fname)
        for key, fname in FONT_FILES.items()
        if os.path.exists(os.path.join(FONT_DIR, fname))
    }

# ─────────────────────────────────────────
# 이미지 생성
# ─────────────────────────────────────────
def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def wrap_text(draw, text, font, max_width):
    """공백 단위로 줄바꿈, 한국어 포함"""
    words = text.split(" ")
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] > max_width and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines

def draw_multiline(draw, lines, font, x, y, fill, line_spacing=14):
    cy = y
    for line in lines:
        draw.text((x, cy), line, font=font, fill=fill)
        cy += font.size + line_spacing
    return cy

def generate_cover(cards_dir, font_paths, today_str):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1080, 1350
    img  = Image.new("RGB", (W, H), color=hex_to_rgb("#f5f0eb"))
    draw = ImageDraw.Draw(img)

    # 장식 원
    for r, alpha in [(420, 20), (300, 30)]:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([(W//2 - r, H//2 - r - 80), (W//2 + r, H//2 + r - 80)],
                   fill=(180, 160, 140, alpha))
        img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
        draw = ImageDraw.Draw(img)

    # 텍스트
    try:
        f_black = ImageFont.truetype(font_paths.get("black", font_paths.get("bold")), 90)
        f_bold  = ImageFont.truetype(font_paths.get("bold",  font_paths.get("regular")), 52)
        f_date  = ImageFont.truetype(font_paths.get("regular"), 32)
    except Exception:
        f_black = f_bold = f_date = ImageFont.load_default()

    sub   = "오늘의"
    title = "AI 뉴스"
    top5  = "TOP 5"

    sw = draw.textbbox((0,0), sub,   font=f_bold)[2]
    tw = draw.textbbox((0,0), title, font=f_black)[2]
    pw = draw.textbbox((0,0), top5,  font=f_bold)[2]

    cy = H // 2 - 160
    draw.text(((W - sw) // 2, cy),        sub,   font=f_bold,  fill=hex_to_rgb("#888888"))
    draw.text(((W - tw) // 2, cy + 70),   title, font=f_black, fill=hex_to_rgb("#1a1a1a"))
    draw.text(((W - pw) // 2, cy + 190),  top5,  font=f_bold,  fill=hex_to_rgb("#c0a080"))

    # 구분선
    lw = 60
    draw.rectangle([(W//2 - lw, cy + 280), (W//2 + lw, cy + 284)],
                   fill=hex_to_rgb("#c8b89a"))

    # 날짜
    dw = draw.textbbox((0,0), today_str, font=f_date)[2]
    draw.text(((W - dw) // 2, cy + 310), today_str, font=f_date, fill=hex_to_rgb("#aaaaaa"))

    # AI Daily 브랜딩
    brand   = "AI Daily"
    try:
        f_brand = ImageFont.truetype(font_paths.get("bold"), 26)
    except Exception:
        f_brand = f_date
    bw = draw.textbbox((0,0), brand, font=f_brand)[2]
    draw.text(((W - bw) // 2, H - 80), brand, font=f_brand, fill=hex_to_rgb("#ccbbaa"))

    path = os.path.join(cards_dir, "card_cover.png")
    img.save(path, "PNG")
    print(f"  ✅ card_cover.png")

def generate_news_card(cards_dir, font_paths, item, idx):
    from PIL import Image, ImageDraw, ImageFont
    W, H   = 1080, 1350
    rank   = item["rank"]
    color  = hex_to_rgb(RANK_COLORS.get(rank, "#888888"))

    img  = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 상단 포인트 컬러 라인
    draw.rectangle([(0, 0), (W, 6)], fill=color)

    # 배경 랭킹 숫자 (장식)
    try:
        f_bg = ImageFont.truetype(font_paths.get("black", font_paths.get("bold")), 320)
    except Exception:
        f_bg = ImageFont.load_default()
    rank_str = f"{rank:02d}"
    bw = draw.textbbox((0,0), rank_str, font=f_bg)[2]
    draw.text((W - bw - 20, 20), rank_str, font=f_bg, fill=(240, 240, 240))

    # 폰트 로드
    try:
        f_rank    = ImageFont.truetype(font_paths.get("black", font_paths.get("bold")), 52)
        f_tag     = ImageFont.truetype(font_paths.get("bold",  font_paths.get("regular")), 26)
        f_title   = ImageFont.truetype(font_paths.get("bold",  font_paths.get("regular")), 46)
        f_summary = ImageFont.truetype(font_paths.get("regular"), 30)
        f_source  = ImageFont.truetype(font_paths.get("regular"), 26)
    except Exception:
        f_rank = f_tag = f_title = f_summary = f_source = ImageFont.load_default()

    PAD = 80

    # 랭킹 번호 (좌상단)
    draw.text((PAD, 60), rank_str, font=f_rank, fill=color)

    # 태그
    tags     = item.get("tags", [])[:2]
    tag_y    = 170
    tag_x    = PAD
    tag_pad  = (10, 6)
    for tag in tags:
        tw_box = draw.textbbox((0,0), tag, font=f_tag)
        tw = tw_box[2] - tw_box[0]
        th = tw_box[3] - tw_box[1]
        rx = [tag_x, tag_y - tag_pad[1],
              tag_x + tw + tag_pad[0]*2, tag_y + th + tag_pad[1]]
        # 배경 (연한 포인트 컬러)
        tag_bg = tuple(min(255, c + 200) for c in color)
        draw.rounded_rectangle(rx, radius=8, fill=tag_bg)
        draw.text((tag_x + tag_pad[0], tag_y), tag, font=f_tag, fill=color)
        tag_x += tw + tag_pad[0]*2 + 12
    tag_y += 52

    # 제목
    title_lines = wrap_text(draw, item["title"], f_title, W - PAD*2)
    title_y     = tag_y + 30
    for line in title_lines[:4]:
        draw.text((PAD, title_y), line, font=f_title, fill=(26, 26, 26))
        title_y += f_title.size + 14

    # 구분선
    sep_y = title_y + 24
    draw.rectangle([(PAD, sep_y), (PAD + 40, sep_y + 3)], fill=color)

    # 요약
    summary_lines = wrap_text(draw, item["summary"], f_summary, W - PAD*2)
    sum_y = sep_y + 36
    for line in summary_lines[:6]:
        draw.text((PAD, sum_y), line, font=f_summary, fill=(136, 136, 136))
        sum_y += f_summary.size + 12

    # 하단: 출처 + 날짜
    footer_y = H - 90
    draw.text((PAD, footer_y), item["source"], font=f_source, fill=(187, 187, 187))
    date_str = item.get("date", "")
    dw = draw.textbbox((0,0), date_str, font=f_source)[2]
    draw.text((W - PAD - dw, footer_y), date_str, font=f_source, fill=(187, 187, 187))

    # 하단 라인
    draw.rectangle([(PAD, H - 50), (W - PAD, H - 48)], fill=(240, 240, 240))

    fname = f"card_{idx:02d}.png"
    img.save(os.path.join(cards_dir, fname), "PNG")
    print(f"  ✅ {fname}  [{item['source']}] {item['title'][:40]}...")

def generate_cards(news_items, today_str):
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa
    except ImportError:
        print("\n⚠️  Pillow 미설치 — 이미지 생성 건너뜀")
        print("   pip install Pillow  으로 설치 후 다시 실행하세요.\n")
        return

    print("\n🖼  인스타 카드 이미지 생성 중...")
    font_paths = ensure_fonts()
    if not font_paths:
        print("  ⚠️  폰트 로드 실패 — 이미지 생성 건너뜀")
        return

    cards_dir = os.path.join(SCRIPT_DIR, "cards")
    os.makedirs(cards_dir, exist_ok=True)

    generate_cover(cards_dir, font_paths, today_str)
    for i, item in enumerate(news_items, 1):
        generate_news_card(cards_dir, font_paths, item, i)

    print(f"\n  📁 저장 위치: {cards_dir}/\n")

# ─────────────────────────────────────────
# 뉴스 수집 / 번역
# ─────────────────────────────────────────
def translate_ko(text):
    if not text:
        return text
    try:
        encoded = urllib.parse.quote(text[:500])
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|ko"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        translated = data.get("responseData", {}).get("translatedText", "")
        if translated and translated.lower() != text.lower():
            return translated
    except Exception:
        pass
    return text

def get_tags(text):
    text_lower = text.lower()
    tags = [tag for tag, kws in TAG_RULES.items() if any(kw in text_lower for kw in kws)]
    return (tags or ["테크"])[:3]

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()[:200]

def parse_date(date_str):
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y.%m.%d"), dt
    except Exception:
        today = datetime.now()
        return today.strftime("%Y.%m.%d"), today

def fetch_feed(feed_info):
    items = []
    try:
        req = urllib.request.Request(
            feed_info["url"],
            headers={"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read())
        for item in root.findall(".//item")[:5]:
            title = item.findtext("title", "").strip()
            link  = item.findtext("link",  "").strip()
            desc  = clean_html(item.findtext("description", ""))
            date_str, dt = parse_date(item.findtext("pubDate", ""))
            if title and link:
                items.append({
                    "title": title, "summary": desc or title,
                    "source": feed_info["source"], "date": date_str,
                    "url": link, "tags": get_tags(title + " " + desc), "_dt": dt,
                })
    except Exception as e:
        print(f"  ⚠️  {feed_info['source']} 실패: {e}")
    return items

# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────
def main():
    today_str = datetime.now().strftime("%Y년 %m월 %d일")

    print("🔍 AI/테크 뉴스 수집 중...\n")
    all_items = []
    for feed in RSS_FEEDS:
        print(f"  → {feed['source']} 불러오는 중...")
        items = fetch_feed(feed)
        print(f"     {len(items)}개 수집")
        all_items.extend(items)

    if not all_items:
        print("\n❌ 수집된 뉴스가 없습니다.")
        return

    all_items.sort(key=lambda x: x["_dt"], reverse=True)
    top5 = all_items[:5]

    print("\n🌐 한국어 번역 중...")
    result = []
    for i, item in enumerate(top5, 1):
        print(f"  번역 중 {i}/5...", end=" ", flush=True)
        title_ko   = translate_ko(item["title"]);  time.sleep(0.5)
        summary_ko = translate_ko(item["summary"]); time.sleep(0.5)
        print("완료")
        result.append({
            "rank": i, "title": title_ko, "summary": summary_ko,
            "source": item["source"], "date": item["date"],
            "url": item["url"], "tags": item["tags"],
        })

    # news.json 저장
    out_path = os.path.join(SCRIPT_DIR, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ news.json 저장 완료 ({len(result)}개)")

    # 인스타 카드 이미지 생성
    generate_cards(result, today_str)

if __name__ == "__main__":
    main()
