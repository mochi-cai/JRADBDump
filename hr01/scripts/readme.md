# MySQL to SQL Server 変換スクリプト

MySQL dump ファイルを SQL Server 用 SQL ファイルに変換するスクリプトです。

## 変換スクリプト

convert_mysql_to_mssql.py

## 使い方

```bash
# 全ファイル変換（デフォルトパス使用）
python hr01/scripts/convert_mysql_to_mssql.py

# 特定ファイルのみ変換
python hr01/scripts/convert_mysql_to_mssql.py hr01_trinfo.sql

# スキーマ名指定
python hr01/scripts/convert_mysql_to_mssql.py --schema dbo

# sqlcmd実行用バッチファイルも出力
python hr01/scripts/convert_mysql_to_mssql.py --sqlcmd

# 入出力パス指定
python hr01/scripts/convert_mysql_to_mssql.py -i ./mysql -o ./mssql

# 全オプション指定
python hr01/scripts/convert_mysql_to_mssql.py --schema dbo --sqlcmd --server 127.0.0.1 --user mochi --password bell0100 --database hr01
```

## オプション一覧

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| files (位置引数) | 全*.sql | 変換対象ファイル名 |
| -i, --input-dir | ./mysql | 入力ディレクトリパス |
| -o, --output-dir | ./mssql | 出力ディレクトリパス |
| --schema | dbo | 出力SQLのスキーマ名 |
| --sqlcmd | 無効 | sqlcmd実行用バッチファイル出力 |
| --server | 127.0.0.1 | SQL Server ホスト |
| --user | mochi | SQL Server ユーザ名 |
| --password | bell0100 | SQL Server パスワード |
| --database | hr01 | SQL Server データベース名 |

## 変換対象ファイル

| ファイル | テーブル | レコード数 | 備考 |
|---------|---------|-----------|------|
| hr01_hinfo.sql | hinfo | 83,391 | 馬名情報 |
| hr01_jinfo.sql | jinfo | 491 | 騎手情報 |
| hr01_pinfo.sql | pinfo | 542 | 競馬場情報 |
| hr01_rinfo.sql | rinfo | 55,925 | レース情報 |
| hr01_routines.sql | - | - | ストアドプロシージャ 6件 |
| hr01_trinfo.sql | trinfo | 548 | 調教師情報 |
| hr01_wk_org.sql | wk_org | 790,848 | レース成績(元データ) |

## 変換内容

- MySQL の型を SQL Server の型に変換（varchar → NVARCHAR, int(N) → INT 等）
- TINYINT → SMALLINT（SQL ServerのTINYINTは正数のみのため）
- 文字列リテラルに N プレフィックスを付与（Unicode 対応）
- エスケープ文字の変換（\' → ''）
- AUTO_INCREMENT → IDENTITY(1,1)
- INSERT を 1000 件ごとのバッチに分割（メモリ節約のためストリーム処理）
- インデックス・主キーの再作成
- ストアドプロシージャ/ファンクションの変換（IN/OUT → @param、BEGIN → AS BEGIN 等）
- sqlcmd実行用バッチファイルの生成（--sqlcmdオプション）

## テーブル個別スクリプト（旧）

以下は個別テーブル用の旧スクリプトです。現在は convert_mysql_to_mssql.py で全テーブル対応しています。

| スクリプト | 対象テーブル |
|---|---|
| convert_hinfo.py | hinfo |
| convert_rinfo.py | rinfo |
| convert_wk_org.py | wk_org |

```bash
python scripts/convert_hinfo.py <入力ファイル> <出力ファイル>
python scripts/convert_rinfo.py <入力ファイル> <出力ファイル>
python scripts/convert_wk_org.py <入力ファイル> <出力ファイル>
```
