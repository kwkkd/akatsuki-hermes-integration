from pathlib import Path
import yaml


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load(self, path: str = ""):
        cfg_path = Path(path or Path(__file__).parent / "akatsuki.yaml")
        if not cfg_path.exists():
            self._data = {}
            self._loaded = True
            return
        with open(cfg_path, encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}
        self._loaded = True

    def __getattr__(self, name):
        if not self._loaded:
            self.load()
        if name == "_data":
            return {}
        if name == "_loaded":
            return False
        return self._data.get(name, {})


CONFIG = Config()
