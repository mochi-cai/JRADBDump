# 目的
MySQLのダンプファイルをSQLServer用に変換する
文字コードはUTF8
テーブル名は変更しない

# 対象のパス
./mysql下の拡張子SQLのファイルが対象
./mssql下に変換ファイルを出力する

# 変換
テーブル作成とデータ投入の変換
ストアドプロシージャ、ストアドファンクションの変換
をする
項目の型にTINYINTを使用すると判断する場合はSMALLINTに変換する。正数しか扱えないので、負の値を扱えない為
変換対象ファイルのサイズが大きい場合を想定して、バッファリングしてメモリの消費を抑える。

## 型変換一覧
| MySQL | SQL Server |
|-------|-----------|
| int(N) | INT |
| bigint(N) | BIGINT |
| smallint(N) | SMALLINT |
| tinyint(N) / tinyint | SMALLINT |
| mediumint(N) | INT |
| varchar(N) | NVARCHAR(N) |
| char(N) | NCHAR(N) |
| text / mediumtext / longtext | NVARCHAR(MAX) |
| blob / mediumblob / longblob | VARBINARY(MAX) |
| float | FLOAT |
| double | FLOAT |
| decimal(M,N) | DECIMAL(M,N) |
| datetime / timestamp | DATETIME2 |
| date | DATE |
| time(N) / time | TIME(N) / TIME |
| boolean / bool | BIT |
| enum(...) | NVARCHAR(50) |
| AUTO_INCREMENT | IDENTITY(1,1) |

## ストアドプロシージャ/ファンクション変換
| MySQL | SQL Server |
|-------|-----------|
| DEFINER=... | (削除) |
| DELIMITER ;; | (削除) |
| IN param type | @param type |
| OUT param type | @param type OUTPUT |
| BEGIN | AS BEGIN |
| 空パラメータリスト () | (削除) |
| CONCAT('a', b) | 'a' + b |
| COLLATE utf8... | (削除) |
| # コメント | -- コメント |
| IF ... THEN ... END IF | IF ... BEGIN ... END |
| WHILE ... DO ... END WHILE | WHILE ... BEGIN ... END |
| hr01.テーブル名 | {schema}.テーブル名 |

# 実行
変換処理は./mysqlをデフォルトの読込パスとするが実行時に明示的に指定をすることで別のパスを可能とする
出力パスは./mssqlをデフォルトの出力パスとするが実行時に明示的に指定をすることで別のパスを可能とする
出力ファイルのスキーマ名は実行時に明示的に指定をすることで動的に変更できることとする
出力ファイルは元ファイル実行時に明示的に指定をすることでsqlcmdでCUIで実行できるように出力パスに別ファイル名で出力する

変換スクリプト: scripts/convert_mysql_to_mssql.py
操作方法: scripts/readme.md を参照

# DB情報
SQLServer接続情報
・IPアドレス127.0.0.1
・ユーザ mochi
・PW bell0100
・データベース hr01

