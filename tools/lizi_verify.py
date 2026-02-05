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


DECOY_OPTIONS = [
    "1999年",
    "2000年",
    "2001年",
    "南京",
    "上海",
    "北京",
    "杭州",
    "10000",
    "12000",
    "15000",
    "20000",
    "河海大学",
    "南京大学",
    "东南大学",
    "软件工程",
    "计算机科学",
    "人工智能",
    "建邺区",
    "鼓楼区",
    "玄武区",
]


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

        decoys = random.sample(DECOY_OPTIONS, 3)
        decoys = [d for d in decoys if d.lower() != correct.lower()][:2]

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
        answer_keys.append({"key": q["key"], "correct": correct})

    return {"success": True, "questions": questions_for_ui, "answer_keys": answer_keys}


def verify(answers: list, answer_keys: list) -> dict:
    """验证答案（不透露哪个错）"""
    if len(answers) != len(answer_keys):
        return {"success": False, "message": "验证失败"}

    correct_count = 0
    for i, ak in enumerate(answer_keys):
        user_answer = answers[i][0] if answers[i] else ""
        if user_answer.strip().lower() == ak["correct"].strip().lower():
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
        result = verify(data["answers"], data["answer_keys"])
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
