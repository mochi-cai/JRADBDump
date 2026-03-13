# MySQL to SQL Server 変換スクリプト

MySQL dump ファイルを SQL Server 用 SQL ファイルに変換するスクリプト群です。

## スクリプト一覧

| スクリプト | 対象テーブル | 説明 |
|---|---|---|
| `convert_hinfo.py` | hinfo | hinfo テーブル専用変換 |
| `convert_rinfo.py` | rinfo | rinfo テーブル専用変換 |
| `convert_wk_org.py` | wk_org | wk_org テーブル専用変換 |
| `convert_mysql_to_mssql.py` | 全テーブル | 汎用変換（CREATE TABLE を自動解析） |

## 使い方

### テーブル個別スクリプト

```bash
python scripts/convert_hinfo.py <入力ファイル> <出力ファイル>
python scripts/convert_rinfo.py <入力ファイル> <出力ファイル>
python scripts/convert_wk_org.py <入力ファイル> <出力ファイル>
```

引数は絶対パス・相対パスどちらでも指定可能です。

```bash
# 相対パス
python scripts/convert_hinfo.py mysql/hr01_hinfo.sql mssql/hr01_hinfo.sql

# 絶対パス
python scripts/convert_hinfo.py c:/home/develop/dbdump/hr01/mysql/hr01_hinfo.sql c:/home/develop/dbdump/hr01/mssql/hr01_hinfo.sql
```

### 汎用スクリプト

```bash
python scripts/convert_mysql_to_mssql.py <入力ディレクトリ> <出力ディレクトリ> [ファイル名...]
```

| 引数 | 必須 | 説明 |
|---|---|---|
| `入力ディレクトリ` | はい | MySQL dump ファイルがあるディレクトリ |
| `出力ディレクトリ` | はい | 変換後の SQL ファイルの出力先（存在しない場合は自動作成） |
| `ファイル名...` | いいえ | 変換対象のファイル名（省略時はディレクトリ内の全 `*.sql`） |

```bash
# ディレクトリ内の全 .sql ファイルを変換
python scripts/convert_mysql_to_mssql.py mysql mssql

# 特定ファイルのみ変換
python scripts/convert_mysql_to_mssql.py mysql mssql hr01_hinfo.sql hr01_rinfo.sql
```

## 変換内容

- MySQL の型を SQL Server の型に変換（`varchar` → `NVARCHAR`, `int(N)` → `INT` 等）
- 文字列リテラルに `N` プレフィックスを付与（Unicode 対応）
- エスケープ文字の変換（`\'` → `''`）
- `AUTO_INCREMENT` → `IDENTITY(1,1)`
- `INSERT` を 1000 件ごとのバッチに分割
- インデックス・主キーの再作成
