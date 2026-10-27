import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs"))

from tools_table import tools_table  # noqa: E402


def test_readme_tool_table_matches_registered_tools():
    readme = (ROOT / "README.md").read_text()
    block = re.search(r"<!-- tools:start -->\n(.*?)\n<!-- tools:end -->", readme, re.S)
    assert block, "README is missing the tools:start/tools:end markers"
    assert block.group(1) == tools_table(), "run: python docs/tools_table.py"
