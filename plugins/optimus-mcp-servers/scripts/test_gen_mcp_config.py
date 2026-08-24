"""一致性校验：生成器从 mcp.config.json 产出的两套配置必须与源码一致且互不冲突。"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
GEN = PLUGIN_DIR / "scripts" / "gen_mcp_config.py"
MCP_JSON = PLUGIN_DIR / ".mcp.json"
CODEX_TOML = PLUGIN_DIR / "config.toml.example"


class GenMcpConfigTest(unittest.TestCase):
    def test_generated_files_are_up_to_date(self):
        r = subprocess.run(
            [sys.executable, str(GEN), "--check"],
            cwd=str(PLUGIN_DIR),
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)

    def test_same_server_set_between_harnesses(self):
        claude = json.loads(MCP_JSON.read_text(encoding="utf-8"))
        codex = CODEX_TOML.read_text(encoding="utf-8")
        codex_names = set()
        for line in codex.splitlines():
            line = line.strip()
            if line.startswith("[mcp_servers.") and line.endswith("]"):
                codex_names.add(line[len("[mcp_servers."):-1])
        claude_names = set(claude["mcpServers"].keys())
        self.assertEqual(claude_names, codex_names)

    def test_codex_has_no_interpolation(self):
        codex = CODEX_TOML.read_text(encoding="utf-8")
        self.assertNotIn("${", codex)

    def test_codex_http_uses_bearer_token_env_var(self):
        codex = CODEX_TOML.read_text(encoding="utf-8")
        self.assertIn("bearer_token_env_var = \"GITHUB_TOKEN\"", codex)

    def test_codex_stdio_uses_env_vars(self):
        codex = CODEX_TOML.read_text(encoding="utf-8")
        self.assertIn("env_vars = [\"MG_MCP_TOKEN\"]", codex)
        self.assertIn("env_vars = [\"MCP_USER_TOKEN\"]", codex)

    def test_claude_http_uses_headers_interpolation(self):
        claude = json.loads(MCP_JSON.read_text(encoding="utf-8"))
        gh = claude["mcpServers"]["github"]
        self.assertEqual(gh["headers"]["Authorization"], "Bearer ${GITHUB_TOKEN}")

    def test_no_argv_token_placeholder(self):
        # 不应再出现依赖 ${VAR} 的 --token 参数（Codex 不展开 ${VAR}）
        claude_txt = MCP_JSON.read_text(encoding="utf-8")
        codex_txt = CODEX_TOML.read_text(encoding="utf-8")
        for txt in (claude_txt, codex_txt):
            self.assertNotIn("--token=${", txt)


if __name__ == "__main__":
    unittest.main()
