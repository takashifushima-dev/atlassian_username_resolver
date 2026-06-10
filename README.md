# Atlassian Username Resolver

Confluenceのフルネームから社員番号（ユーザーID）を取得するMCPサーバーです。Claude CLIから利用できます。

## 概要

このMCPサーバーは、Confluence上のユーザーのフルネーム（例: "TAKASHI FUSHIMA"）から社員番号（例: "J0144971"）を取得します。
全ユーザー情報を30日間キャッシュすることで、高速な検索を実現しています。

## 機能

- フルネームから社員番号への変換
- Confluence全ユーザー情報の自動取得とキャッシュ

## 必要要件

- Python 3.13以上
- Confluence（オンプレミス版）へのアクセス権限

## セットアップ

### 1. 設定ファイルの作成

"atlassian_username_resolver_v1.0\config.json.template"をコピーし、内容を書き換えconfig.jsonとして保存：

```json
{
  "url": "https://your-confluence-url/confluence",
  "username": "your-employee-id",
  "password": "your-password"
}
```

- `url`: ConfluenceのベースURL
- `username`: 社員番号（ログイン時に使用するID）
- `password`: ログインパスワード

**重要**: `config.json` には認証情報が含まれるため、Gitにコミットしないでください。このファイルは `.gitignore` に含まれています。

### 2. 依存パッケージのインストール

#### Windows環境
```bash
pip install -r requirements.txt
```

#### WSL/Linux環境（uvを使用）
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Claude CLIへの登録

### Windows環境での登録手順

```bash
cd c:\repos\atlassian_username_resolver_release
claude mcp add atlassian-username-resolver c:\repos\atlassian_username_resolver_release\.venv\Scripts\python.exe c:\repos\atlassian_username_resolver_release\main.py
```

### WSL環境での登録手順

```bash
cd /mnt/c/repos/atlassian_username_resolver_release
claude mcp add atlassian-username-resolver /mnt/c/repos/atlassian_username_resolver_release/.venv/bin/python /mnt/c/repos/atlassian_username_resolver_release/main.py
```

### 登録確認

```bash
claude mcp list
```

以下のように表示されればOK：
```
atlassian-username-resolver: ... - ✓ Connected
```

## 使い方

### Claude CLIでの使用

```bash
claude
```

チャットで以下のようにリクエスト：

```
「TAKASHI FUSHIMAの社員番号を教えて」
→ J0144971

「KAKERU TAKECHIの社員番号は？」
→ J0144969
```

### 他のMCPサーバーとの連携

既存の `mcp-atlassian` などと組み合わせて使用できます：

```
「KAKERU TAKECHIのConfluence文書を検索してください」
```

## 仕組み

### 初回実行時

1. Confluence APIから全ユーザー情報を取得（約30秒）
2. フルネーム→社員番号のマッピングを作成
3. `user_mapping.json` に保存（更新日時付き）
4. 検索実行

### 2回目以降

1. `user_mapping.json` の更新日時をチェック
2. 30日以内なら既存データを使用（即座に結果を返す）
3. 30日以上経過していれば再取得

## ファイル構成

```
atlassian_username_resolver_release/
├── main.py                    # MCPサーバーエントリーポイント
├── mapping_manager.py          # ユーザーマッピング管理
├── username_searcher.py        # ユーザー名検索ロジック
├── requirements.txt            # Python依存パッケージ
├── config.json                 # 設定ファイル（要作成、Gitには含めない）
├── user_mapping.json           # ユーザーマッピングキャッシュ（自動生成）
└── README.md                   # このファイル
```

## トラブルシューティング

### 接続エラーが出る場合

プロキシ設定を確認してください。環境変数 `HTTP_PROXY` と `HTTPS_PROXY` が設定されていれば自動的に使用されます。

### config.jsonが見つからないエラー

`config.json` がこのディレクトリに存在することを確認してください。テンプレートに従って作成してください。

### 認証エラーが出る場合

`config.json` の `username` と `password` が正しいことを確認してください。