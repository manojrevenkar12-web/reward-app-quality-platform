import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "raq"
PLATFORM = ["testing", "rollout", "triage", "service"]


def _imports(path: Path) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def test_the_platform_never_reads_the_truth():
    for pkg in PLATFORM:
        for f in (ROOT / pkg).rglob("*.py"):
            bad = {m for m in _imports(f) if m.startswith(("raq.world", "raq.sim"))}
            assert not bad, f"{f.relative_to(ROOT)} imports {bad}"


def test_the_world_does_not_read_the_platforms_settings():
    for f in (ROOT / "world").rglob("*.py"):
        src = f.read_text()
        for name in ("platform", "value", "gate"):
            assert f'load("{name}")' not in src
        assert not {m for m in _imports(f) if m.startswith("raq.") and m != "raq.keyed"}
