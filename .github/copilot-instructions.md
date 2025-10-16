## 目的
このリポジトリは将棋の棋譜とコメントを整形・処理する一連のスクリプト群です。
AI コーディング支援者は以下の「このプロジェクト固有の常識」を知ることで、素早く有用な変更や機能追加が行えます。

## 重要なファイルと役割（必ず参照すること）
- `gemini_clean_batch_mode4.py` : Gemini（genai）を使ったバッチ処理の主力スクリプト。API呼び出し、JSONL作成、ファイルアップロード、バッチジョブ作成の流れを持つ。
- `gemini_clean*.py` 系（例: `gemini_clean.py`, `gemini_clean_batch.py`, `gemini_clean_reason2_moves.py`）: 類似の処理ロジックや旧バージョンが多数ある。変更は横展開の影響を考慮する。
- `prompt_comment.py` : JSONから手のコメントを抽出してテキスト化するユーティリティ。データ形状の参照に有用。
- `setting.py` : PyGame を使った GUI 用設定（画面サイズ、画像読み込み等）。UI変更時に参照。
- `DataSet/` : 入力となる JSON ファイル群（各局のデータ）。
- `ProcessedComments_reason/` と `ProcessedComments_reason_memo/` : 出力先ディレクトリ（整形結果とメモログ）。

## データ形状（必須知識）
- 各入力 JSON は少なくとも以下のキーを持つ:
  - `sente`: 先手の名前 (文字列)
  - `gote`: 後手の名前 (文字列)
  - `moves`: 配列。各要素は `move_number` と `comments` を含む。`comments` は文字列または文字列リスト。
- スクリプトは `move_number` と `comments` を抽出して `(move_number, comment_text)` ペアのリストに変換して処理する。

## 実行ワークフロー（要注意）
- バッチランナーは `gemini_clean_batch_mode4.py` の `main()` を直接実行することで動く。主な入出力:
  - 入力: `./DataSet/*.json`
  - 出力（期待）: `./ProcessedComments_reason/<base>_processed.txt`
  - memo: `./ProcessedComments_reason_memo/<base>_memo.txt`
- Gemini API の利用は環境変数 `GEMINI_API_KEY` に依存する。Windows PowerShell の一時設定例:

```powershell
$env:GEMINI_API_KEY = "YOUR_KEY"
python .\gemini_clean_batch_mode4.py
```

## API / 外部依存と注意点
- Google genai ライブラリを使っている。`genai.Client(api_key=...)` で初期化される。
- `client.files.upload(...)` と `client.batches.create(...)` の組合せで JSONL をアップロードし、バッチ処理を開始する設計。
- バッチ作成はクォータ切れや 429 応答が発生しやすい（ログにもその痕跡あり）。対処方針:
  - APIキーをハードコーディングしない。必ず環境変数経由で扱う。
  - 再試行（指数バックオフ）、レートリミット時のファイル削除やクリーンアップを追加する。
  - 開発/デバッグ時は `make_jsonl_file` と `write_jsonl_file` で生成される `<base>_request.jsonl` を確認する。

## プロンプト / 出力パターン（重要）
- `GEMINI_PROMPT_TEMPLATE` 変数に大きなテンプレートが格納されている。プロンプトは
  - 上部: 指示（テンプレートの先頭）
  - 下部: 実際のコメント一覧（`手数N: コメント` の行）
 という parts に分けて送信している（`types.Part.from_text` を使用）。この分割を壊すと期待通りの応答にならない。
- レスポンスは `手数N:` 単位で分割してパースしている（正規表現）。AI側のフォーマット逸脱があればフォールバック動作が走るので、フォーマット変更時はパーサも更新すること。

## コーディングルール / 慣習（プロジェクト固有）
- 日本語コメント・変数名混在は普通（コード内は英語・日本語混在）。出力やログは日本語で十分。
- デバッグ用に生成する JSONL / 出力ファイルを利用してローカルでの検証を行う。`*_request.jsonl` を人手で確認してから実APIを叩くこと。
- 既存スクリプトは冗長に類似ファイルが多い。新機能はまず一つのファイルで作り、影響範囲を限定してから横展開する。

## よくある修正候補（優先度高）
- 429/QUOTA_EXCEEDED に対する再試行と遅延（backoff）を `gemini_clean_batch_mode4.py` に組み込む。
- エラーハンドリング: `client.batches.create` が失敗したときの削除処理はあるが、ログ出力を改善し、失敗ファイルの再試行ログを残す。
- `make_jsonl_file` の返り値（requests）をユニットテスト可能な形にして、パース・プロンプト生成のテストを追加する。

## 参考になる箇所（実例）
- プロンプトテンプレート: `gemini_clean_batch_mode4.py` の `GEMINI_PROMPT_TEMPLATE`。
- JSON 抽出例: `prompt_comment.py` の `extract_comments`。
- File/batch API 呼び出し例: `gemini_clean_batch_mode4.py` の `client.files.upload` と `client.batches.create`。

## 最後に
このファイルを起点に、小さな変更（ログ追加、再試行、JSONLの検証）を行って結果を確認してください。変更案を作成したら、このファイルへの追記で「何を検証したか」を短く記載してください。

---
フィードバック: 不明点や追加して欲しい実例（例: 代表的な入力 JSON の抜粋）があれば教えてください。
