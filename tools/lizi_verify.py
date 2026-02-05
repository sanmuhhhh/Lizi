#!/usr/bin/env python3
import json
import sys
import random
from pathlib import Path
from cryptography.fernet import Fernet
from hashlib import sha256
import base64

LIZI_DIR = Path.home() / ".config/lizi"
VERIFY_FILE = LIZI_DIR / "secrets" / "verify.enc"
KEY_SEED = "lizi-sanmu-2026"


def get_key():
    hash_bytes = sha256(KEY_SEED.encode()).digest()
    return base64.urlsafe_b64encode(hash_bytes)


def load_questions():
    if not VERIFY_FILE.exists():
        return None
    fernet = Fernet(get_key())
    encrypted = VERIFY_FILE.read_bytes()
    decrypted = fernet.decrypt(encrypted)
    return json.loads(decrypted.decode())


def save_questions(data):
    VERIFY_FILE.parent.mkdir(parents=True, exist_ok=True)
    fernet = Fernet(get_key())
    encrypted = fernet.encrypt(json.dumps(data).encode())
    VERIFY_FILE.write_bytes(encrypted)


DECOY_POOLS = {
    "city": ["上海", "北京", "杭州", "苏州", "合肥", "武汉", "广州", "深圳"],
    "county": ["凤阳县", "明光市", "天长市", "来安县", "全椒县"],
    "university": ["南京大学", "东南大学", "南京航空航天大学", "南京理工大学"],
    "date": ["8月15号", "10月1号", "3月20号", "12月25号", "5月4号"],
    "color": ["红色", "蓝色", "黑色", "白色", "粉色", "紫色"],
    "name": ["刘思琪", "王欣怡", "陈雨萱", "林佳琪", "周诗涵", "吴梦洁"],
    "default": ["不确定", "想不起来", "好像是..."],
}

KEY_TO_POOL = {
    "parents_city": "city",
    "hometown": "county",
    "university": "university",
    "birthday": "date",
    "favorite_color": "color",
    "crush": "name",
}


PENDING_FILE = LIZI_DIR / "secrets" / "pending_verify.enc"


def pick_questions(count: int = 3) -> dict:
    stored = load_questions()
    if not stored:
        return {"success": False, "message": "未设置验证问题"}

    all_q = stored["questions"]
    if len(all_q) < count:
        count = len(all_q)

    picked = random.sample(all_q, count)

    questions_for_ui = []
    answer_keys = []

    for q in picked:
        correct = q["answer"]
        key = q["key"]

        pool_name = KEY_TO_POOL.get(key, "default")
        pool = DECOY_POOLS.get(pool_name, DECOY_POOLS["default"])
        decoys = [d for d in pool if d.lower() != correct.lower()]
        decoys = random.sample(decoys, min(2, len(decoys)))

        options = [
            {"label": "不知道", "description": ""},
        ] + [{"label": d, "description": ""} for d in decoys]

        random.shuffle(options)

        questions_for_ui.append(
            {
                "question": q["question"],
                "header": q["key"][:30],
                "options": options,
                "multiple": False,
                "custom": True,
            }
        )
        answer_keys.append(
            {"key": q["key"], "correct": correct, "aliases": q.get("aliases", [])}
        )

    fernet = Fernet(get_key())
    encrypted = fernet.encrypt(json.dumps(answer_keys).encode())
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    PENDING_FILE.write_bytes(encrypted)

    return {"success": True, "questions": questions_for_ui}


def normalize_answer(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("月", "-").replace("号", "").replace("日", "")
    s = s.replace("县", "").replace("市", "").replace("区", "")
    return s


def to_pinyin(s: str) -> str:
    try:
        from pypinyin import lazy_pinyin

        return "".join(lazy_pinyin(s)).lower()
    except:
        return s.lower()


def to_pinyin_initials(s: str) -> str:
    try:
        from pypinyin import lazy_pinyin

        return "".join([p[0] for p in lazy_pinyin(s) if p]).lower()
    except:
        return s.lower()


def get_initials_from_pinyin(s: str) -> str:
    try:
        from pypinyin import lazy_pinyin

        return "".join([p[0] for p in lazy_pinyin(s) if p]).lower()
    except:
        pass

    s = s.lower().strip()
    initials = []
    i = 0
    while i < len(s):
        if s[i].isalpha():
            initials.append(s[i])
            while i < len(s) and s[i].isalpha() and s[i] not in "aeiou":
                i += 1
            while i < len(s) and s[i].isalpha():
                i += 1
        else:
            i += 1
    return "".join(initials) if len(initials) > 1 else s


def answers_match(user: str, correct: str) -> bool:
    user_norm = normalize_answer(user)
    correct_norm = normalize_answer(correct)
    user_lower = user.strip().lower()
    correct_lower = correct.strip().lower()

    if user_norm == correct_norm:
        return True
    if to_pinyin(user) == to_pinyin(correct):
        return True
    if user_lower == correct_lower:
        return True
    if user_lower == to_pinyin(correct):
        return True
    if to_pinyin(user) == correct_lower:
        return True
    if user_lower == to_pinyin_initials(correct):
        return True
    if to_pinyin_initials(user) == to_pinyin_initials(correct):
        return True
    if user_lower == get_initials_from_pinyin(correct):
        return True
    return False


def verify(answers: list) -> dict:
    if not PENDING_FILE.exists():
        return {"success": False, "message": "没有待验证的问题"}

    try:
        fernet = Fernet(get_key())
        encrypted = PENDING_FILE.read_bytes()
        decrypted = fernet.decrypt(encrypted)
        answer_keys = json.loads(decrypted.decode())
        PENDING_FILE.unlink()
    except:
        return {"success": False, "message": "验证数据已过期"}

    if len(answers) != len(answer_keys):
        return {"success": False, "message": "验证失败"}

    correct_count = 0
    for i, ak in enumerate(answer_keys):
        user_answer = answers[i][0] if answers[i] else ""
        correct = ak["correct"]
        aliases = ak.get("aliases", [])

        matched = answers_match(user_answer, correct)
        if not matched:
            for alias in aliases:
                if answers_match(user_answer, alias):
                    matched = True
                    break

        if matched:
            correct_count += 1

    if correct_count == len(answer_keys):
        return {"success": True, "message": "验证通过"}
    else:
        return {"success": False, "message": "验证失败"}


def setup(questions: list) -> dict:
    """设置验证问题
    格式: [{"key": "birthday", "question": "伞木生日是哪天", "answer": "1月1日"}, ...]
    """
    if len(questions) < 3:
        return {"success": False, "message": "至少需要3个验证问题"}

    save_questions({"questions": questions})
    return {"success": True, "message": f"已设置 {len(questions)} 个验证问题"}


def get_status() -> dict:
    stored = load_questions()
    if not stored:
        return {"ready": False, "count": 0, "message": "未设置验证问题"}
    count = len(stored["questions"])
    ready = count >= 3
    return {
        "ready": ready,
        "count": count,
        "message": "验证系统就绪"
        if ready
        else f"问题不足，需要至少3个（当前{count}个）",
    }


def add_question(question: dict) -> dict:
    stored = load_questions()
    if not stored:
        stored = {"questions": []}

    existing_keys = [q["key"] for q in stored["questions"]]
    if question["key"] in existing_keys:
        for i, q in enumerate(stored["questions"]):
            if q["key"] == question["key"]:
                stored["questions"][i] = question
                break
        save_questions(stored)
        return {
            "success": True,
            "message": f"已更新问题: {question['key']}",
            "count": len(stored["questions"]),
        }

    stored["questions"].append(question)
    save_questions(stored)
    return {
        "success": True,
        "message": f"已添加问题: {question['key']}",
        "count": len(stored["questions"]),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "需要指定模式: pick/verify/setup/status"}))
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "pick":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        result = pick_questions(count)
        print(json.dumps(result, ensure_ascii=False))

    elif mode == "verify":
        data = json.loads(sys.stdin.read())
        result = verify(data["answers"])
        print(json.dumps(result, ensure_ascii=False))

    elif mode == "setup":
        questions = json.loads(sys.stdin.read())
        result = setup(questions)
        print(json.dumps(result, ensure_ascii=False))

    elif mode == "status":
        result = get_status()
        print(json.dumps(result, ensure_ascii=False))

    elif mode == "add":
        question = json.loads(sys.stdin.read())
        result = add_question(question)
        print(json.dumps(result, ensure_ascii=False))

    else:
        print(json.dumps({"error": f"未知模式: {mode}"}))
        sys.exit(1)
