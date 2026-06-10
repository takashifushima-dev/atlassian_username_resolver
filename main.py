"""
Atlassian Username Resolver — MCP server for Claude.

Resolves Atlassian user identities (display name ↔ accountId ↔ email) via
the Jira and Confluence REST APIs.

Required configuration file (config.json):
    {
        "url": "https://your-org.atlassian.net/confluence",
        "username": "your-username-or-employee-id",
        "password": "your-password"
    }
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from username_searcher import search_employee_id

mcp = FastMCP("atlassian-username-resolver")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        raise RuntimeError(
            f"config.json not found at {config_path}. "
            "Please create it with url, username, and password."
        )
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


_CONFIG = _load_config()


def _base() -> str:
    url = _CONFIG.get("url", "").rstrip("/")
    if not url:
        raise RuntimeError("url is not set in config.json")
    return url


def _auth() -> tuple[str, str]:
    user = _CONFIG.get("username", "")
    password = _CONFIG.get("password", "")
    if not user or not password:
        raise RuntimeError(
            "username and password are required in config.json"
        )
    return user, password


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_employee_id_from_name(display_name: str) -> str:
    """
    フルネーム（displayName）から社員番号（employee ID）を取得します。
    マッピングファイルが30日以内なら既存のデータを使用、
    それ以外の場合はConfluence APIから全ユーザー情報を取得して更新します。

    Args:
        display_name: ユーザーのフルネーム（例: "TAKASHI FUSHIMA"）
    Returns:
        社員番号（例: "J0144971"）。見つからない場合は空文字列。
    """
    mapping_path = Path(__file__).parent / "user_mapping.json"
    confluence_url = _base()
    username, password = _auth()

    return search_employee_id(
        display_name=display_name,
        mapping_file_path=mapping_path,
        confluence_url=confluence_url,
        username=username,
        password=password
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
