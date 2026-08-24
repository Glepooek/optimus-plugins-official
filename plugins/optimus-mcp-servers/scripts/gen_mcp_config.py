#!/usr/bin/env python3
"""
从 mcp.config.json 生成两套 harness 各自的 MCP 配置（单一真源，避免两侧漂移）：
  - .mcp.json            -> Claude Code（headers/env 用 ${VAR} 插值）
  - config.toml.example  -> Codex（bearer_token_env_var / env_vars，不依赖 ${VAR} 插值）

用法：
  python scripts/gen_mcp_config.py            # 就地重新生成（默认）
  python scripts/gen_mcp_config.py --check    # 只校验产物与源码一致，不写盘
"""
import argparse
import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
SOURCE = PLUGIN_DIR / "mcp.config.json"
MCP_JSON = PLUGIN_DIR / ".mcp.json"
CODEX_TOML = PLUGIN_DIR / "config.toml.example"


def load():
    with open(SOURCE, encoding="utf-8") as f:
        return json.load(f)


def render_claude(cfg):
    """Claude Code 的 .mcp.json：HTTP 用 headers+${VAR}，stdio 用 env+${VAR}。"""
    servers = {}
    for name, s in cfg["servers"].items():
        if s["transport"] == "http":
            servers[name] = {
                "type": "http",
                "url": s["url"],
                "headers": {"Authorization": "Bearer ${%s}" % s["bearer"]},
            }
        else:  # stdio
            entry = {"command": s["command"], "args": list(s["args"])}
            env = {}
            for var in s.get("env", []):
                env[var] = "${%s}" % var
            if env:
                entry["env"] = env
            servers[name] = entry
    return {"mcpServers": servers}


def render_codex(cfg):
    """Codex 的 config.toml：HTTP 用 bearer_token_env_var，stdio 用 env_vars 转发环境变量。"""
    lines = [
        "# ~/.codex/config.toml",
        "# Optimus MCP 服务器配置（Codex 原生字段，不使用变量字符串插值）。",
        "# 由 scripts/gen_mcp_config.py 从 mcp.config.json 生成，请勿手改。",
        "#",
        "# 运行 Codex 前需在当前环境 export 以下变量（或用 shell_environment_policy.set 注入）：",
    ]
    for var, desc in cfg["env_vars"].items():
        lines.append("#   %-16s %s" % (var, desc))
    lines.append("")
    for name, s in cfg["servers"].items():
        lines.append("[mcp_servers.%s]" % name)
        if s["transport"] == "http":
            lines.append('url = "%s"' % s["url"])
            lines.append('bearer_token_env_var = "%s"' % s["bearer"])
        else:
            lines.append('command = "%s"' % s["command"])
            args = ", ".join(json.dumps(a, ensure_ascii=False) for a in s["args"])
            lines.append("args = [%s]" % args)
            if s.get("env"):
                vals = ", ".join(json.dumps(v, ensure_ascii=False) for v in s["env"])
                lines.append("env_vars = [%s]" % vals)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验生成产物是否与源码一致")
    args = ap.parse_args()

    cfg = load()
    expected_mcp = json.dumps(render_claude(cfg), ensure_ascii=False, indent=2) + "\n"
    expected_toml = render_codex(cfg)

    if args.check:
        ok = True
        for path, expected in ((MCP_JSON, expected_mcp), (CODEX_TOML, expected_toml)):
            if path.read_text(encoding="utf-8") != expected:
                ok = False
                print("MISMATCH: %s" % path)
                print("---- expected ----")
                print(expected)
        if not ok:
            sys.exit(1)
        print("OK: 生成产物与 mcp.config.json 一致。")
        return

    MCP_JSON.write_text(expected_mcp, encoding="utf-8")
    CODEX_TOML.write_text(expected_toml, encoding="utf-8")
    print("已重新生成 .mcp.json 与 config.toml.example")


if __name__ == "__main__":
    main()
