"""Hermes-compatible tool registration."""

from ..chat.tools import AkatsukiToolRegistry, _builtin_registry


def register_all():
    try:
        from hermes_agent import tool_registry
    except ImportError:
        return

    registry = AkatsukiToolRegistry()
    for tool_schema in _builtin_registry.list_tools():
        tool_registry.register(tool_schema["function"])
