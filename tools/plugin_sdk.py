import importlib
import importlib.util
import inspect
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Optional

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


class PluginBase:
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    schema: dict = {}

    def __init__(self):
        self._loaded = False

    def load(self):
        self._loaded = True

    def unload(self):
        self._loaded = False

    def execute(self, action: str, params: dict) -> dict:
        raise NotImplementedError("Plugin must implement execute()")

    def validate(self, action: str, params: dict) -> Optional[str]:
        return None


class PluginManager:
    def __init__(self, plugin_dir: str = ""):
        self._plugins: dict[str, PluginBase] = {}
        self._plugin_dir = Path(plugin_dir or self._default_dir())
        self._plugin_dir.mkdir(parents=True, exist_ok=True)

    def _default_dir(self) -> str:
        return os.environ.get(
            "AKATSUKI_PLUGIN_DIR",
            str(Path(__file__).resolve().parent.parent / "plugins"),
        )

    def discover(self) -> list[str]:
        found = []
        for f in self._plugin_dir.glob("*.py"):
            if f.stem.startswith("_"):
                continue
            found.append(f.stem)
        return found

    def load_plugin(self, name: str) -> Optional[PluginBase]:
        if name in self._plugins:
            return self._plugins[name]
        spec = importlib.util.spec_from_file_location(
            f"akatsuki_plugin_{name}",
            self._plugin_dir / f"{name}.py",
        )
        if not spec or not spec.loader:
            logger.warning(f"Plugin not found: {name}")
            return None
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, PluginBase) and attr is not PluginBase:
                    instance = attr()
                    instance.load()
                    self._plugins[name] = instance
                    logger.info(f"Loaded plugin: {name} v{instance.version}")
                    return instance
            logger.warning(f"No PluginBase subclass in {name}")
            return None
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
            return None

    def unload_plugin(self, name: str):
        plugin = self._plugins.pop(name, None)
        if plugin:
            plugin.unload()
            logger.info(f"Unloaded plugin: {name}")

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        return self._plugins.get(name)

    def list_plugins(self) -> list[dict]:
        return [
            {
                "name": p.name or name,
                "description": p.description,
                "version": p.version,
                "author": p.author,
                "loaded": p._loaded,
            }
            for name, p in self._plugins.items()
        ]

    def execute(self, plugin_name: str, action: str, params: dict) -> dict:
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return {"error": f"Plugin not loaded: {plugin_name}"}
        if not plugin._loaded:
            return {"error": f"Plugin not loaded: {plugin_name}"}
        validation_error = plugin.validate(action, params)
        if validation_error:
            return {"error": f"Validation failed: {validation_error}"}
        try:
            return plugin.execute(action, params)
        except Exception as e:
            logger.exception(f"Plugin {plugin_name} execute error")
            return {"error": str(e)}


_manager = PluginManager()


def get_manager() -> PluginManager:
    return _manager


AKATSUKI_PLUGIN_SCHEMA = {
    "name": "akatsuki_plugin",
    "description": "AKATSUKI Plugin System — load, list, and execute external plugins dynamically. Plugins are Python files in the plugins/ directory that extend AKATSUKI functionality.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "load", "unload", "execute", "discover"],
                "description": "Plugin action",
            },
            "plugin_name": {
                "type": "string",
                "description": "Plugin name (filename without .py)",
            },
            "plugin_action": {
                "type": "string",
                "description": "Action to pass to plugin's execute()",
            },
            "params": {
                "type": "string",
                "description": "JSON params for plugin execution",
            },
        },
        "required": ["action"],
    },
}


def akatsuki_plugin(action: str, plugin_name: str = "", plugin_action: str = "",
                    params: str = "{}") -> str:
    mgr = get_manager()

    if action == "discover":
        found = mgr.discover()
        return tool_result({"plugins_found": found})

    if action == "list":
        plugins = mgr.list_plugins()
        discovered = mgr.discover()
        return tool_result({
            "loaded": plugins,
            "available": discovered,
        })

    if action == "load":
        if not plugin_name:
            return tool_error("plugin_name is required")
        plugin = mgr.load_plugin(plugin_name)
        if plugin:
            return tool_result({"loaded": True, "name": plugin_name, "version": plugin.version})
        return tool_error(f"Failed to load plugin: {plugin_name}")

    if action == "unload":
        if not plugin_name:
            return tool_error("plugin_name is required")
        mgr.unload_plugin(plugin_name)
        return tool_result({"unloaded": True, "name": plugin_name})

    if action == "execute":
        if not plugin_name or not plugin_action:
            return tool_error("plugin_name and plugin_action are required")
        try:
            parsed_params = json.loads(params) if isinstance(params, str) else params
        except json.JSONDecodeError:
            return tool_error("Invalid params JSON")
        result = mgr.execute(plugin_name, plugin_action, parsed_params)
        return tool_result(result)

    return tool_error(f"Unknown action: {action}")


def check_akatsuki_plugin_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_plugin",
    toolset="akatsuki",
    schema=AKATSUKI_PLUGIN_SCHEMA,
    handler=lambda args, **kw: akatsuki_plugin(
        action=args["action"],
        plugin_name=args.get("plugin_name", ""),
        plugin_action=args.get("plugin_action", ""),
        params=args.get("params", "{}"),
    ),
    check_fn=check_akatsuki_plugin_requirements,
    emoji="🧩",
)