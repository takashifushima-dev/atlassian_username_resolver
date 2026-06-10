"""
User mapping management for Confluence users.
Handles fetching, caching, and updating user mappings.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

# 定数
API_PAGE_LIMIT = 100  # 1回のAPIリクエストで取得するユーザー数
MAX_PAGES = 3000  # 最大ページ数（無限ループ防止）
CACHE_EXPIRY_DAYS = 30  # キャッシュの有効期限（日数）


def fetch_all_users(base_url: str, username: str, password: str) -> dict[str, str]:
    """
    Confluenceから全ユーザーを取得し、フルネーム→社員番号のマッピングを作成

    Args:
        base_url: Confluence URL (e.g. "https://example.com/confluence")
        username: 認証用ユーザー名
        password: 認証用パスワード
    Returns:
        フルネーム→社員番号の辞書
    """
    mappings = {}
    start = 0
    page_count = 0

    while page_count < MAX_PAGES:
        page_count += 1
        # CQLで全ユーザーを取得
        try:
            resp = httpx.get(
                f"{base_url}/rest/api/search",
                params={"cql": "type=user", "start": start, "limit": API_PAGE_LIMIT},
                auth=(username, password),
                headers={"Accept": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error at start={start}, limit={API_PAGE_LIMIT}: {e}")
            raise
        data = resp.json()

        results = data.get("results", []) if isinstance(data, dict) else []
        if not results:
            break

        for result in results:
            user = result.get("user", {})
            display_name = user.get("displayName", "")
            user_name = user.get("username", "")
            if display_name and user_name:
                mappings[display_name] = user_name

        # 次のページがあるかチェック
        if len(results) < API_PAGE_LIMIT:
            break
        start += API_PAGE_LIMIT

    if page_count >= MAX_PAGES:
        logger.warning(f"Reached MAX_PAGES={MAX_PAGES}, fetched {len(mappings)} users")

    return mappings


def load_mapping_from_file(file_path: Path) -> tuple[dict[str, str], bool]:
    """
    user_mapping.jsonを読み込み、1ヶ月以内かチェック

    Args:
        file_path: マッピングファイルのパス
    Returns:
        (mappings, is_fresh): マッピング辞書と、30日以内ならTrueのタプル
    """
    if not file_path.exists():
        return {}, False

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        last_updated_str = data.get("metadata", {}).get("last_updated", "")
        if not last_updated_str:
            return data.get("mappings", {}), False

        # 更新日時をパース
        last_updated = datetime.fromisoformat(last_updated_str)
        now = datetime.now()
        days_old = (now - last_updated).days

        # キャッシュの有効期限内なら新鮮
        is_fresh = days_old < CACHE_EXPIRY_DAYS
        return data.get("mappings", {}), is_fresh
    except Exception as e:
        logger.warning(f"Failed to load mapping from {file_path}: {e}", exc_info=True)
        return {}, False


def update_mapping_file(file_path: Path, mappings: dict[str, str]) -> None:
    """
    user_mapping.jsonを更新

    Args:
        file_path: マッピングファイルのパス
        mappings: フルネーム→社員番号の辞書
    """
    data = {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "description": "Confluence user full name to employee ID mapping",
            "total_users": len(mappings)
        },
        "mappings": mappings
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
