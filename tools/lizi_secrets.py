#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from cryptography.fernet import Fernet
from hashlib import sha256
import base64

LIZI_DIR = Path.home() / ".config/lizi"
SECRETS_FILE = LIZI_DIR / "secrets" / "private.enc"
KEY_SEED = "lizi-sanmu-private-2026"


def get_key():
    hash_bytes = sha256(KEY_SEED.encode()).digest()
    return base64.urlsafe_b64encode(hash_bytes)


def load_secrets():
    if not SECRETS_FILE.exists():
        return {}
    fernet = Fernet(get_key())
    encrypted = SECRETS_FILE.read_bytes()
    decrypted = fernet.decrypt(encrypted)
    return json.loads(decrypted.decode())


def save_secrets(data):
    SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    fernet = Fernet(get_key())
    encrypted = fernet.encrypt(json.dumps(data).encode())
    SECRETS_FILE.write_bytes(encrypted)


def set_secret(key: str, value: str, description: str = "") -> dict:
    secrets = load_secrets()
    secrets[key] = {"value": value, "description": description}
    save_secrets(secrets)
    return {"success": True, "message": f"已保存: {key}"}


def get_secret(key: str) -> dict:
    secrets = load_secrets()
    if key not in secrets:
        return {"success": False, "message": f"未找到: {key}"}
    return {
        "success": True,
        "key": key,
        "value": secrets[key]["value"],
        "description": secrets[key].get("description", ""),
    }


def list_secrets() -> dict:
    secrets = load_secrets()
    keys = [
        {"key": k, "description": v.get("description", "")} for k, v in secrets.items()
    ]
    return {"success": True, "count": len(keys), "keys": keys}


def delete_secret(key: str) -> dict:
    secrets = load_secrets()
    if key not in secrets:
        return {"success": False, "message": f"未找到: {key}"}
    del secrets[key]
    save_secrets(secrets)
    return {"success": True, "message": f"已删除: {key}"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "需要指定模式: set/get/list/delete"}))
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "set":
        data = json.loads(sys.stdin.read())
        result = set_secret(data["key"], data["value"], data.get("description", ""))
        print(json.dumps(result, ensure_ascii=False))

    elif mode == "get":
        key = sys.argv[2] if len(sys.argv) > 2 else json.loads(sys.stdin.read())["key"]
        result = get_secret(key)
        print(json.dumps(result, ensure_ascii=False))

    elif mode == "list":
        result = list_secrets()
        print(json.dumps(result, ensure_ascii=False))

    elif mode == "delete":
        key = sys.argv[2] if len(sys.argv) > 2 else json.loads(sys.stdin.read())["key"]
        result = delete_secret(key)
        print(json.dumps(result, ensure_ascii=False))

    else:
        print(json.dumps({"error": f"未知模式: {mode}"}))
        sys.exit(1)
