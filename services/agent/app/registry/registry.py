import json, os
from typing import Dict, Any, List

TOOLS_PATH = os.getenv("TOOL_REGISTRY_PATH", "/app/registry/tools.json")

class ToolRegistry:
    def __init__(self):
        with open(TOOLS_PATH, "r") as f:
            self.tools = {t["name"]: t for t in json.load(f)}

    def list_tools(self) -> List[Dict[str, Any]]:
        return list(self.tools.values())

    def get_tool(self, name: str) -> Dict[str, Any] | None:
        return self.tools.get(name)
