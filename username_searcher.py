"""
Username search functionality.
Handles searching employee IDs from display names with caching.
"""

import logging
from pathlib import Path

import httpx

from mapping_manager import fetch_all_users, load_mapping_from_file, update_mapping_file

logger = logging.getLogger(__name__)


def search_employee_id(
    display_name: str,
    mapping_file_path: Path,
    confluence_url: str,
    username: str,
    password: str
) -> str:
    """
    フルネーム（displayName）から社員番号（employee ID）を取得します。
    マッピングファイルがキャッシュ有効期限内なら既存のデータを使用、
    それ以外の場合はConfluence APIから全ユーザー情報を取得して更新します。

    Args:
        display_name: ユーザーのフルネーム（例: "TAKASHI FUSHIMA"）
        mapping_file_path: マッピングファイルのパス
        confluence_url: Confluence URL
        username: 認証用ユーザー名
        password: 認証用パスワード
    Returns:
        社員番号（例: "J0144971"）。見つからない場合は空文字列。
    Raises:
        RuntimeError: Confluence APIからのユーザー取得に失敗した場合
    """
    # 既存のマッピングをチェック
    mappings, is_fresh = load_mapping_from_file(mapping_file_path)

    # キャッシュ有効期限切れ、または存在しない場合は更新
    if not is_fresh:
        try:
            mappings = fetch_all_users(confluence_url, username, password)
            update_mapping_file(mapping_file_path, mappings)
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch users from Confluence: {e}")
            raise RuntimeError(
                f"Confluence APIからのユーザー取得に失敗しました: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching users: {e}")
            raise RuntimeError(
                f"ユーザー情報の取得中に予期しないエラーが発生しました: {e}"
            ) from e

    # マッピングから検索
    return mappings.get(display_name, "")
