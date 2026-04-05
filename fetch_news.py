#!/usr/bin/env python3
"""
AI/테크 뉴스 TOP5 수집기
RSS 피드에서 최신 뉴스를 가져와 news.json에 저장합니다.
사용법: python3 fetch_news.py
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

# RSS 피드 목록 (AI/테크 전문 매체)
RSS_FEEDS = [
    {"url": "https://venturebeat.com/category/ai/feed/",        "source": "VentureBeat"},
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "source": "TechCrunch"},
    {"url": "https://www.theverge.com/rss/index.xml",           "source": "The Verge"},
    {"url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "source": "Ars Technica"},
    {"url": "https://www.wired.com/feed/tag/ai/rss",            "source": "WIRED"},
]

# 키워드 → 태그 매핑
TAG_RULES = {
    "AI":      ["artificial intelligence", " ai ", "machine learning", "neural", "deep learning"],
    "LLM":     ["gpt", "claude", "gemini", "llama", "language model", "chatgpt", "openai", "anthropic"],
    "로보틱스":  ["robot", "robotics", "humanoid", "autonomous"],
    "반도체":   ["chip", "semiconductor", "nvidia", "gpu", "tpu", "npu"],
    "빅테크":   ["google", "microsoft", "apple", "amazon", "meta", "tesla"],
    "스타트업": ["startup", "funding", "raises", "series", "venture"],
    "오픈소스": ["open source", "open-source", "github", "hugging face"],
    "보안":    ["security", "privacy", "hack", "vulnerability", "breach"],
    "규제":    ["regulation", "law", "policy", "ban", "eu", "congress"],
    "연구":    ["research", "paper", "study", "benchmark", "dataset"],
}

def translate_ko(text):
    """MyMemory 무료 번역 API (API 키 불필요)"""
    if not text:
        return text
    try:
        encoded = urllib.parse.quote(text[:500])
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|ko"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        translated = data.get("responseData", {}).get("translatedText", "")
        # 번역 실패 또는 원문 반환 시 원문 사용
        if translated and translated.lower() != text.lower():
            return translated
    except Exception:
        pass
    return text

def get_tags(text):
    text_lower = text.lower()
    tags = []
    for tag, keywords in TAG_RULES.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    if not tags:
        tags = ["테크"]
    return tags[:3]

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:200]

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
            content = resp.read()
        root = ET.fromstring(content)

        # RSS 2.0
        for item in root.findall(".//item")[:5]:
            title = item.findtext("title", "").strip()
            link  = item.findtext("link", "").strip()
            desc  = clean_html(item.findtext("description", ""))
            pub   = item.findtext("pubDate", "")
            date_str, dt = parse_date(pub)

            if title and link:
                items.append({
                    "title": title,
                    "summary": desc or title,
                    "source": feed_info["source"],
                    "date": date_str,
                    "url": link,
                    "tags": get_tags(title + " " + desc),
                    "_dt": dt,
                })
    except Exception as e:
        print(f"  ⚠️  {feed_info['source']} 실패: {e}")
    return items

def main():
    print("🔍 AI/테크 뉴스 수집 중...\n")
    all_items = []

    for feed in RSS_FEEDS:
        print(f"  → {feed['source']} 불러오는 중...")
        items = fetch_feed(feed)
        print(f"     {len(items)}개 수집")
        all_items.extend(items)

    if not all_items:
        print("\n❌ 수집된 뉴스가 없습니다. 인터넷 연결을 확인해주세요.")
        return

    # 최신순 정렬 → TOP 5
    all_items.sort(key=lambda x: x["_dt"], reverse=True)
    top5 = all_items[:5]

    print("\n🌐 한국어 번역 중...")
    result = []
    for i, item in enumerate(top5, 1):
        print(f"  번역 중 {i}/5...", end=" ", flush=True)
        title_ko   = translate_ko(item["title"])
        time.sleep(0.5)  # API 속도 제한 대응
        summary_ko = translate_ko(item["summary"])
        time.sleep(0.5)
        print("완료")
        result.append({
            "rank":    i,
            "title":   title_ko,
            "summary": summary_ko,
            "source":  item["source"],
            "date":    item["date"],
            "url":     item["url"],
            "tags":    item["tags"],
        })

    script_dir = __import__("os").path.dirname(__file__)
    out_path   = __import__("os").path.join(script_dir, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ news.json 업데이트 완료! ({len(result)}개)\n")
    for item in result:
        print(f"  {item['rank']}. [{item['source']}] {item['title'][:60]}...")

if __name__ == "__main__":
    main()
