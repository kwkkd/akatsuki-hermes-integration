import hashlib
import hmac
import json
import base64
import time
import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("akatsuki.auth")


ROLES = {
    "admin": {"permissions": ["*"], "priority": 100},
    "operator": {
        "permissions": [
            "note/read", "note/write", "note/list", "note/search",
            "note/delete", "folder/list", "tags/list",
            "tool/recon", "tool/payload", "tool/evasion",
            "tool/c2", "tool/vuln", "tool/chain", "tool/report",
            "tool/dept", "sync/trigger",
        ],
        "priority": 50,
    },
    "analyst": {
        "permissions": [
            "note/read", "note/list", "note/search", "folder/list", "tags/list",
            "tool/recon", "tool/vuln", "tool/dept", "tool/report",
        ],
        "priority": 20,
    },
    "viewer": {
        "permissions": [
            "note/read", "note/list", "folder/list", "tags/list",
        ],
        "priority": 10,
    },
}


@dataclass
class User:
    username: str
    password_hash: str
    role: str = "viewer"
    enabled: bool = True
    created: float = 0.0

    def has_permission(self, permission: str) -> bool:
        role_perms = ROLES.get(self.role, ROLES["viewer"])["permissions"]
        if "*" in role_perms:
            return True
        if permission in role_perms:
            return True
        for rp in role_perms:
            if rp.endswith("*") and permission.startswith(rp.rstrip("*")):
                return True
        return False


def hash_password(password: str, salt: str = "") -> str:
    salt = salt or os.urandom(16).hex()
    return salt + ":" + hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(password: str, stored: str) -> bool:
    if ":" not in stored:
        return False
    salt, h = stored.split(":", 1)
    return h == hashlib.sha256((salt + password).encode()).hexdigest()


def generate_jwt(payload: dict, secret: str, expiry: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    full = payload.copy()
    full["iat"] = int(time.time())
    full["exp"] = int(time.time()) + expiry
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(json.dumps(full).encode()).rstrip(b"=").decode()
    sig = hmac.new(secret.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).hexdigest()
    return f"{header_b64}.{payload_b64}.{sig}"


def verify_jwt(token: str, secret: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        expected_sig = hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, parts[2]):
            return None
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


class AuthManager:
    def __init__(self, config: dict = None):
        self._users: dict[str, User] = {}
        self._secret = config.get("jwt_secret", "akatsuki-default-secret-change-me") if config else "akatsuki-default-secret-change-me"
        self._token_expiry = config.get("token_expiry", 3600) if config else 3600
        self._load_default_users()

    def _load_default_users(self):
        self._users["admin"] = User(
            username="admin",
            password_hash=hash_password("akatsuki-admin"),
            role="admin",
            created=time.time(),
        )

    def add_user(self, username: str, password: str, role: str = "viewer") -> User:
        if username in self._users:
            raise ValueError(f"User already exists: {username}")
        if role not in ROLES:
            raise ValueError(f"Invalid role: {role}")
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            created=time.time(),
        )
        self._users[username] = user
        return user

    def authenticate(self, username: str, password: str) -> Optional[str]:
        user = self._users.get(username)
        if not user or not user.enabled:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return generate_jwt({"sub": username, "role": user.role}, self._secret, self._token_expiry)

    def validate_token(self, token: str) -> Optional[dict]:
        payload = verify_jwt(token, self._secret)
        if not payload:
            return None
        username = payload.get("sub")
        user = self._users.get(username)
        if not user or not user.enabled:
            return None
        return {"username": username, "role": user.role, "permissions": ROLES.get(user.role, ROLES["viewer"])["permissions"]}

    def check_permission(self, token: str, permission: str) -> bool:
        session = self.validate_token(token)
        if not session:
            return False
        role_perms = ROLES.get(session["role"], ROLES["viewer"])["permissions"]
        if "*" in role_perms:
            return True
        if permission in role_perms:
            return True
        for rp in role_perms:
            if rp.endswith("*") and permission.startswith(rp.rstrip("*")):
                return True
        return False

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def list_users(self) -> list[dict]:
        return [
            {"username": u.username, "role": u.role, "enabled": u.enabled}
            for u in self._users.values()
        ]

    def from_config(self, config: dict):
        self._secret = config.get("jwt_secret", self._secret)
        self._token_expiry = config.get("token_expiry", self._token_expiry)
        for user_cfg in config.get("users", []):
            username = user_cfg.get("username")
            password = user_cfg.get("password")
            role = user_cfg.get("role", "viewer")
            if username and password:
                try:
                    self.add_user(username, password, role)
                except ValueError:
                    pass