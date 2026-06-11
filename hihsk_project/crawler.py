# -*- coding: utf-8 -*-
"""
Crawl + parse toan bo du lieu cong khai tu hihsk.com.

4 loai noi dung:
  vocabulary   -> bang lessons / vocabulary / sentences / definitions
  conversation -> bang conversation_lessons
  radical      -> bang radical_details
  thpt         -> bang thpt_questions

Quy trinh moi loai:
  1. Goi API theo id (bo qua 401/403 tra phi, dung khi gap nhieu 404 lien tiep)
  2. Luu JSON tho vao raw_json/{loai}/{id}.json  (an toan)
  3. Parse va nap vao bang DB tuong ung

Co the chay lai bat ky luc nao: id da co trong DB se tu bo qua (resume).
Neu da co san file trong raw_json/, dung che do parse-local de khoi goi API lai.
"""

import os
import json
import time
import requests

import config
import database as db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR  = os.path.join(BASE_DIR, "raw_json")

HEADERS = {
    "User-Agent": config.USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi,en;q=0.9",
    "Referer": "https://hihsk.com/",
    "Origin": "https://hihsk.com",
}


def J(v):
    if v in (None, ""): return None
    if isinstance(v, str): return v
    return json.dumps(v, ensure_ascii=False)


# ==================== GOI API ====================

def fetch(loai, item_id):
    """Tra ve (data, status): 'ok' | 'empty' | 'paid' | 'error'."""
    url = config.API + config.ENDPOINTS[loai].format(id=item_id)
    try:
        r = requests.get(url, headers=HEADERS, timeout=config.TIMEOUT)
        if r.status_code == 404:
            return None, "empty"
        if r.status_code in (401, 403):
            return None, "paid"
        r.raise_for_status()
        data = r.json()
        if not data:
            return None, "empty"
        return data, "ok"
    except Exception as e:
        print(f"  [!] {loai} {item_id} loi: {e}")
        return None, "error"


def save_raw(loai, item_id, data):
    d = os.path.join(RAW_DIR, loai)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{item_id}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== PARSE TUNG LOAI ====================

def parse_vocabulary(file_id, data):
    """Tu vung: nap vao lessons + vocabulary + sentences + definitions."""
    sub = data.get("subcate") or {}
    db.save_lesson({
        "lesson_id": file_id, "cate": data.get("cate"),
        "name": sub.get("name"), "lang_vi": sub.get("lang_vi"),
        "des": sub.get("des"), "conversation": sub.get("conversation"),
        "fill_data_json": J(sub.get("fill_data_json")),
        "subcates_json": J(data.get("subcates")),
    })
    saved = 0
    for v in data.get("vocals", []):
        vid = v.get("id")
        saved += db.save_vocab({
            "vocab_id": vid, "lesson_id": file_id,
            "hanzi": v.get("vocabulary"), "hanzi_phon": v.get("vocabulary_tran"),
            "pinyin": v.get("pinyin"), "han_viet": v.get("han_viet"),
            "meaning_vi": v.get("lang_vi"), "meaning_en": v.get("lang_en"),
            "measure_word": v.get("measure_word"), "antonym": v.get("antonym"),
            "image_url": v.get("image"), "audio_mp3": v.get("mp3"),
            "char_detail_json": J(v.get("character_detail")),
        })
        for s in (v.get("sentences") or []):
            db.save_sentence({
                "sent_id": s.get("id"), "vocab_id": vid, "lesson_id": file_id,
                "text": s.get("name"), "pinyin": s.get("pinyin"),
                "lang_vi": s.get("lang_vi"), "lang_en": s.get("lang_en"),
                "audio_mp3": s.get("mp3"),
            })
        for d in (v.get("definitions") or []):
            db.save_definition({
                "def_id": d.get("id"), "vocab_id": vid, "lesson_id": file_id,
                "part_of_speech": d.get("part_of_speech"),
                "meaning_vi": d.get("meaning_vi"), "meaning_en": d.get("meaning_en"),
                "senses_json": J(d.get("senses_json")),
            })
    return saved


def parse_conversation(file_id, data):
    n = 0
    for item in (data.get("data") or []):
        n += db.save_conversation_lesson({
            "id": item.get("id"), "file_id": file_id,
            "number_lesson": item.get("number_lesson"),
            "lang_vi": item.get("lang_vi"), "lang_en": item.get("lang_en"),
            "lesson_data": J(item.get("lesson_data")),
            "test_data": J(item.get("test_data")),
        })
    return n


def parse_radical(file_id, data):
    n = 0
    for group in (data.get("data") or []):
        title = group.get("title")
        content = group.get("content") or {}
        items = content.get("data") if isinstance(content, dict) else None
        for it in (items or []):
            known = {"lang_vi","mean","pinyin","hanzi","netbut","image","mp3","common_words"}
            extra = {k: val for k, val in it.items() if k not in known}
            cw = it.get("common_words")
            n += db.save_radical_detail({
                "file_id": file_id, "group_title": title,
                "hanzi": it.get("hanzi"), "pinyin": it.get("pinyin"),
                "lang_vi": it.get("lang_vi"), "mean": it.get("mean"),
                "netbut": it.get("netbut"), "image": it.get("image"),
                "mp3": it.get("mp3"),
                "common_words": ", ".join(cw) if isinstance(cw, list) else J(cw),
                "extra_json": J(extra),
            })
    return n


def parse_thpt(file_id, data):
    n = 0
    for exam in (data.get("exam") or []):
        title, year, eid = exam.get("title"), exam.get("year"), exam.get("id")
        for p in ["part1","part2","part3","part4","part5"]:
            for q in (exam.get(p) or []):
                n += db.save_thpt_question({
                    "exam_id": eid, "exam_title": title, "year": year,
                    "part": p, "q_id": q.get("id"), "question": q.get("question"),
                    "answer": q.get("answer"), "opt_a": q.get("A"),
                    "opt_b": q.get("B"), "opt_c": q.get("C"), "opt_d": q.get("D"),
                    "explain1": q.get("explain1"), "translate_vi": q.get("translate_vi"),
                })
    return n


def parse_reading(file_id, data):
    d = data.get("data") or {}
    cj = d.get("content_json") or {}
    db.save_reading_lesson({
        "reading_id": d.get("id") or file_id,
        "name": d.get("name"),
        "passage": cj.get("passage") or d.get("content"),
    })
    n = 0
    for q in (cj.get("questions") or []):
        qtype = q.get("type")
        if qtype == "dictation_input":
            answer = q.get("correct_answer")
        elif qtype == "matching_pairs":
            answer = J(q.get("pairs"))
        else:
            ci = q.get("correct_index")
            choices = q.get("choices") or []
            answer = (choices[ci] if (ci is not None and ci < len(choices))
                      else q.get("translation"))
        db.save_reading_question({
            "reading_id": d.get("id") or file_id,
            "q_num": q.get("question_number"),
            "q_type": qtype,
            "question": q.get("question"),
            "choices": J(q.get("choices")),
            "answer": answer,
        })
        n += 1
    return n


def parse_exam(file_id, data, level=None):
    n = 0
    for exam in (data.get("exam") or []):
        eid = exam.get("id") or file_id
        ename = exam.get("name")
        for p in ["part1","part2","part3","part4","part5","part6"]:
            for q in (exam.get(p) or []):
                db.save_exam_question({
                    "exam_id": eid, "level": level, "exam_name": ename,
                    "part": p, "q_id": q.get("id"),
                    "question": q.get("question"), "answer": q.get("answer"),
                    "opt_a": q.get("A"), "opt_b": q.get("B"),
                    "opt_c": q.get("C"), "opt_d": q.get("D"),
                    "explain1": q.get("explain"),
                    "translate_vi": q.get("translate_vi"),
                    "mp3": q.get("mp3"), "image": q.get("image"),
                })
                n += 1
    return n


def parse_sentence(file_id, data):
    n = 0
    for it in (data.get("data") or []):
        db.save_sentence_sample({
            "sample_id": it.get("id"),
            "subcate_id": it.get("subcate_id") or file_id,
            "title": it.get("title"), "cn": it.get("cn"),
            "pinyin": it.get("pinyin"), "lang_vi": it.get("lang_vi"),
            "json_question": J(it.get("json_question")),
            "words_json": J(it.get("data")),
        })
        n += 1
    return n


PARSERS = {
    "vocabulary":   parse_vocabulary,
    "conversation": parse_conversation,
    "radical":      parse_radical,
    "thpt":         parse_thpt,
    "reading":      parse_reading,
    "sentence":     parse_sentence,
}

DONE_CHECK = {
    "vocabulary":   db.vocab_lesson_done,
    "conversation": db.conversation_done,
    "radical":      db.radical_done,
    "thpt":         db.thpt_done,
    "reading":      db.reading_done,
    "sentence":     db.sentence_done,
}


# ==================== CRAWL 1 LOAI (goi API) ====================

def crawl_loai(loai):
    start, end = config.SCAN_RANGES[loai]
    print(f"\n=== Crawl {loai}: id {start}-{end} ===")
    total = miss = 0
    for item_id in range(start, end + 1):
        if DONE_CHECK[loai](item_id):
            print(f"[skip] {loai} {item_id} da co")
            continue
        data, status = fetch(loai, item_id)
        if status == "paid":
            print(f"[$$]  {loai} {item_id} tra phi -> bo qua")
            db.log(loai, item_id, 0, "paid")
            time.sleep(config.DELAY_SEC); continue
        if status == "empty":
            miss += 1
            print(f"[--]  {loai} {item_id} rong (miss {miss}/{config.MAX_MISS})")
            if miss >= config.MAX_MISS:
                print(f"Dung {loai} (qua nhieu id rong).")
                break
            time.sleep(config.DELAY_SEC); continue
        if status == "error":
            db.log(loai, item_id, 0, "error")
            time.sleep(config.DELAY_SEC * 2); continue
        miss = 0
        save_raw(loai, item_id, data)
        saved = PARSERS[loai](item_id, data)
        db.log(loai, item_id, saved, "ok")
        total += saved
        print(f"[ok]  {loai} {item_id}: {saved} muc (tong {total})")
        time.sleep(config.DELAY_SEC)
    print(f"Xong {loai}: {total} muc.")
    return total


# ==================== PARSE LAI TU raw_json/ (khong goi API) ====================

def parse_local(loai):
    """Doc lai file da tai trong raw_json/{loai}/ va nap vao DB.
    Dua vao INSERT IGNORE o tang DB de tranh trung, nen chay lai an toan.
    Rieng vocabulary: doc them file cu kieu raw_json/vocal-list-N.json."""
    pairs = []   # (file_id, duong_dan)

    d = os.path.join(RAW_DIR, loai)
    if os.path.isdir(d):
        for f in sorted(x for x in os.listdir(d) if x.endswith(".json")):
            pairs.append((int(f.replace(".json", "")), os.path.join(d, f)))

    # File cu cua vocabulary nam thang trong raw_json/
    if loai == "vocabulary" and os.path.isdir(RAW_DIR):
        for f in sorted(os.listdir(RAW_DIR)):
            if f.startswith("vocal-list-") and f.endswith(".json"):
                fid = int(f.replace("vocal-list-", "").replace(".json", ""))
                pairs.append((fid, os.path.join(RAW_DIR, f)))

    if not pairs:
        print(f"[--] chua co file cho {loai}")
        return 0

    total = 0
    for file_id, path in pairs:
        data = json.load(open(path, encoding="utf-8"))
        total += PARSERS[loai](file_id, data)
    print(f"[ok] {loai}: nap {total} muc tu {len(pairs)} file local")
    return total


def crawl_exam():
    """Luyen thi HSK: endpoint can level. Quet tung level x tung id."""
    start, end = config.SCAN_RANGES["exam"]
    print(f"\n=== Crawl exam (luyen thi HSK): level {config.EXAM_LEVELS}, id {start}-{end} ===")
    total = 0
    for level in config.EXAM_LEVELS:
        miss = 0
        print(f"\n-- Level HSK {level} --")
        for exam_id in range(start, end + 1):
            if db.exam_done(exam_id):
                continue
            url = config.API + config.ENDPOINTS["exam"].format(level=level, id=exam_id)
            try:
                r = requests.get(url, headers=HEADERS, timeout=config.TIMEOUT)
                if r.status_code in (401, 403):
                    print(f"[$$]  exam L{level} {exam_id} tra phi")
                    time.sleep(config.DELAY_SEC); continue
                if r.status_code == 404:
                    miss += 1
                    if miss >= config.MAX_MISS:
                        print(f"  het bai o level {level}.")
                        break
                    time.sleep(config.DELAY_SEC); continue
                r.raise_for_status()
                data = r.json()
                if not data or not data.get("exam"):
                    miss += 1
                    if miss >= config.MAX_MISS:
                        break
                    time.sleep(config.DELAY_SEC); continue
            except Exception as e:
                print(f"  [!] exam L{level} {exam_id} loi: {e}")
                time.sleep(config.DELAY_SEC * 2); continue
            miss = 0
            save_raw("exam", exam_id, data)
            saved = parse_exam(exam_id, data, level=level)
            db.log("exam", exam_id, saved, "ok")
            total += saved
            print(f"[ok]  exam L{level} {exam_id}: {saved} cau (tong {total})")
            time.sleep(config.DELAY_SEC)
    print(f"\nXong exam: {total} cau.")
    return total


def crawl_all():
    for loai in ["vocabulary", "conversation", "radical", "thpt", "reading", "sentence"]:
        crawl_loai(loai)
    crawl_exam()
