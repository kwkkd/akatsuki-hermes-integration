from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from enum import IntEnum
import json


class MessageType:
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"
    STREAM = "stream"
    PING = "ping"
    PONG = "pong"


class ErrorCode(IntEnum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    NOT_AUTHORIZED = -32001
    NOTE_NOT_FOUND = -32002
    SYNC_CONFLICT = -32003
    RATE_LIMITED = -32004
    TIMEOUT = -32005


class OpType(IntEnum):
    INSERT = 0
    DELETE = 1
    UPDATE = 2
    MERGE = 3


class SyncStrategy:
    FULL = "full"
    INCREMENTAL = "incremental"
    LIVE = "live"


@dataclass
class JsonRpcRequest:
    jsonrpc: str = "2.0"
    id: str = ""
    method: str = ""
    params: Any = None

    def to_dict(self):
        d = {"jsonrpc": self.jsonrpc, "id": self.id, "method": self.method}
        if self.params is not None:
            d["params"] = self.params
        return d

    def to_json(self):
        return json.dumps(self.to_dict())


@dataclass
class JsonRpcResponse:
    jsonrpc: str = "2.0"
    id: str = ""
    result: Any = None
    error: Optional[dict] = None

    def to_dict(self):
        d = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            d["error"] = self.error
        if self.result is not None:
            d["result"] = self.result
        return d

    def to_json(self):
        return json.dumps(self.to_dict())


@dataclass
class Note:
    id: str = ""
    path: str = ""
    title: str = ""
    content: str = ""
    tags: list = field(default_factory=list)
    links: list = field(default_factory=list)
    frontmatter: dict = field(default_factory=dict)
    checksum: str = ""
    version: int = 0
    created: int = 0
    modified: int = 0
    source: str = "user"


@dataclass
class CrdtOperation:
    op_id: str = ""
    op_type: OpType = OpType.INSERT
    node_id: str = ""
    seq: int = 0
    lamport: int = 0
    position: Optional[int] = None
    length: Optional[int] = None
    value: Optional[str] = None
    path: Optional[list] = None
    deps: list = field(default_factory=list)
