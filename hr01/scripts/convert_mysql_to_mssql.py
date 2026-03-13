"""
MySQL dump ファイルを SQL Server 用に変換するスクリプト

使い方:
    python convert_mysql_to_mssql.py                                    # ./mysql 内の *.sql を全て変換 -> ./mssql
    python convert_mysql_to_mssql.py -i ./mysql -o ./mssql              # パス明示
    python convert_mysql_to_mssql.py file1.sql                          # 指定ファイルのみ変換
    python convert_mysql_to_mssql.py file1.sql --schema hr01            # スキーマ名指定
    python convert_mysql_to_mssql.py file1.sql --sqlcmd                 # sqlcmd実行用ファイルも出力
    python convert_mysql_to_mssql.py file1.sql --sqlcmd --server 127.0.0.1 --user mochi --password bell0100 --database hr01
"""

import re
import sys
import os
import glob
import argparse


def parse_create_table(content):
    """CREATE TABLE 文を解析してテーブル名、カラム情報、キー情報を返す"""
    m = re.search(r'CREATE TABLE `(\w+)` \((.*?)\)\s*ENGINE=', content, re.DOTALL)
    if not m:
        return None, [], [], None
    table_name = m.group(1)
    body = m.group(2)

    columns = []
    keys = []
    primary_key = None

    for line in body.split('\n'):
        line = line.strip().rstrip(',')
        if not line:
            continue

        # PRIMARY KEY
        pk_m = re.match(r'PRIMARY KEY \(`(.+?)`\)', line)
        if pk_m:
            primary_key = [c.strip().strip('`') for c in pk_m.group(1).split(',')]
            continue

        # UNIQUE KEY
        uk_m = re.match(r'UNIQUE KEY `(\w+)` \(`(.+?)`\)', line)
        if uk_m:
            key_name = uk_m.group(1)
            key_cols = [c.strip().strip('`') for c in uk_m.group(2).split(',')]
            keys.append(('UNIQUE', key_name, key_cols))
            continue

        # KEY (index)
        k_m = re.match(r'KEY `(\w+)` \(`(.+?)`\)', line)
        if k_m:
            key_name = k_m.group(1)
            key_cols = [c.strip().strip('`') for c in k_m.group(2).split(',')]
            keys.append(('INDEX', key_name, key_cols))
            continue

        # Column definition
        col_m = re.match(r'`(\w+)`\s+(.+)', line)
        if col_m:
            col_name = col_m.group(1)
            col_def = col_m.group(2)
            is_auto = 'AUTO_INCREMENT' in col_def
            mssql_def = convert_column_type(col_def)
            columns.append((col_name, mssql_def, is_auto))

    return table_name, columns, keys, primary_key


def convert_column_type(mysql_def):
    """MySQL のカラム定義を SQL Server 用に変換"""
    d = mysql_def

    # CHARACTER SET / COLLATE 削除
    d = re.sub(r'\s*CHARACTER SET \w+', '', d)
    d = re.sub(r'\s*COLLATE \w+', '', d)

    # AUTO_INCREMENT 削除 (別途 IDENTITY として処理)
    d = re.sub(r'\s*AUTO_INCREMENT', '', d)

    # 型変換
    # int(N) -> INT
    d = re.sub(r'\bint\(\d+\)', 'INT', d, flags=re.IGNORECASE)
    d = re.sub(r'\bbigint\(\d+\)', 'BIGINT', d, flags=re.IGNORECASE)
    # smallint(N) -> SMALLINT
    d = re.sub(r'\bsmallint\(\d+\)', 'SMALLINT', d, flags=re.IGNORECASE)
    # tinyint(N) -> SMALLINT (SQL Server の TINYINT は正数のみなので SMALLINT に変換)
    d = re.sub(r'\btinyint\(\d+\)', 'SMALLINT', d, flags=re.IGNORECASE)
    d = re.sub(r'\btinyint\b', 'SMALLINT', d, flags=re.IGNORECASE)
    # mediumint(N) -> INT
    d = re.sub(r'\bmediumint\(\d+\)', 'INT', d, flags=re.IGNORECASE)

    # varchar(N) -> NVARCHAR(N)
    d = re.sub(r'\bvarchar\((\d+)\)', r'NVARCHAR(\1)', d, flags=re.IGNORECASE)
    # char(N) -> NCHAR(N)
    d = re.sub(r'\bchar\((\d+)\)', r'NCHAR(\1)', d, flags=re.IGNORECASE)

    # text -> NVARCHAR(MAX)
    d = re.sub(r'\blongtext\b', 'NVARCHAR(MAX)', d, flags=re.IGNORECASE)
    d = re.sub(r'\bmediumtext\b', 'NVARCHAR(MAX)', d, flags=re.IGNORECASE)
    d = re.sub(r'\btext\b', 'NVARCHAR(MAX)', d, flags=re.IGNORECASE)

    # blob -> VARBINARY(MAX)
    d = re.sub(r'\blongblob\b', 'VARBINARY(MAX)', d, flags=re.IGNORECASE)
    d = re.sub(r'\bmediumblob\b', 'VARBINARY(MAX)', d, flags=re.IGNORECASE)
    d = re.sub(r'\bblob\b', 'VARBINARY(MAX)', d, flags=re.IGNORECASE)

    # float -> FLOAT
    d = re.sub(r'\bfloat\b', 'FLOAT', d, flags=re.IGNORECASE)
    # double -> FLOAT
    d = re.sub(r'\bdouble\b', 'FLOAT', d, flags=re.IGNORECASE)
    # decimal(M,N) -> DECIMAL(M,N)
    d = re.sub(r'\bdecimal\((\d+),(\d+)\)', r'DECIMAL(\1,\2)', d, flags=re.IGNORECASE)

    # datetime -> DATETIME2 (must come before date/time)
    d = re.sub(r'\bdatetime\b', 'DATETIME2', d, flags=re.IGNORECASE)
    # timestamp -> DATETIME2
    d = re.sub(r'\btimestamp\b', 'DATETIME2', d, flags=re.IGNORECASE)
    # date -> DATE
    d = re.sub(r'\bdate\b', 'DATE', d, flags=re.IGNORECASE)
    # time(N) -> TIME(N)
    d = re.sub(r'\btime\((\d+)\)', r'TIME(\1)', d, flags=re.IGNORECASE)
    d = re.sub(r'\btime\b', 'TIME', d, flags=re.IGNORECASE)

    # boolean / bool -> BIT
    d = re.sub(r'\bboolean\b', 'BIT', d, flags=re.IGNORECASE)
    d = re.sub(r'\bbool\b', 'BIT', d, flags=re.IGNORECASE)

    # enum -> NVARCHAR(50) (簡易対応)
    d = re.sub(r"enum\([^)]+\)", 'NVARCHAR(50)', d, flags=re.IGNORECASE)

    # DEFAULT NULL -> NULL, DEFAULT 'val' はそのまま
    d = re.sub(r'\bDEFAULT NULL\b', 'NULL', d, flags=re.IGNORECASE)
    d = re.sub(r"\bDEFAULT\s+'([^']*)'\s*", r"DEFAULT '\1' ", d, flags=re.IGNORECASE)

    return d.strip()


def parse_values(values_str):
    """INSERT 文の VALUES 部分をタプルのリストに分割"""
    tuples = []
    i = 0
    length = len(values_str)
    while i < length:
        if values_str[i] == '(':
            j = i + 1
            in_quote = False
            while j < length:
                c = values_str[j]
                if c == '\\' and in_quote and j + 1 < length and values_str[j + 1] == "'":
                    j += 2  # skip escaped quote
                    continue
                if c == "'":
                    in_quote = not in_quote
                elif c == ')' and not in_quote:
                    tuples.append(values_str[i:j + 1])
                    i = j + 1
                    break
                j += 1
            else:
                i = j
        else:
            i += 1
    return tuples


def convert_tuple(t):
    """1つのタプルの値を SQL Server 用に変換"""
    inner = t[1:-1]
    vals = []
    ci = 0
    current = ''
    in_q = False
    length = len(inner)

    while ci < length:
        ch = inner[ci]
        if ch == '\\' and ci + 1 < length and inner[ci + 1] == "'":
            # MySQL \' -> SQL Server ''
            current += "''"
            ci += 2
            continue
        elif ch == '\\' and ci + 1 < length and inner[ci + 1] == '\\':
            # MySQL \\\\ -> \\
            current += '\\\\'
            ci += 2
            continue
        elif ch == "'":
            in_q = not in_q
            current += ch
        elif ch == ',' and not in_q:
            vals.append(current.strip())
            current = ''
        else:
            current += ch
        ci += 1
    vals.append(current.strip())

    new_vals = []
    for v in vals:
        if v == 'NULL':
            new_vals.append('NULL')
        elif v.startswith("'"):
            new_vals.append('N' + v)
        else:
            new_vals.append(v)

    return '(' + ', '.join(new_vals) + ')'


def extract_create_table_section(input_path):
    """ファイル先頭部分から CREATE TABLE 文を抽出する（メモリ節約）"""
    lines = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            lines.append(line)
            # ENGINE= が見つかったら CREATE TABLE 終了
            if 'ENGINE=' in line:
                break
            # 安全策: 200行以内に見つからなければ打ち切り
            if len(lines) > 200:
                break
    return ''.join(lines)


def extract_routines(input_path):
    """ストアドプロシージャ・ストアドファンクションを抽出する"""
    routines = []
    in_routine = False
    routine_lines = []
    routine_type = None
    routine_name = None

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            # DELIMITER 行を検出
            if line.strip().startswith('DELIMITER'):
                delimiter = line.strip().split()[-1] if len(line.strip().split()) > 1 else ''
                if delimiter == ';;' or delimiter == '//':
                    in_routine = True
                    routine_lines = []
                    continue
                elif delimiter == ';':
                    # ルーチン終了
                    if in_routine and routine_lines:
                        routines.append((routine_type, routine_name, ''.join(routine_lines)))
                    in_routine = False
                    routine_lines = []
                    routine_type = None
                    routine_name = None
                    continue

            if in_routine:
                # ルーチン定義開始を検出
                proc_m = re.match(r'CREATE\s+(?:DEFINER\s*=\s*\S+\s+)?PROCEDURE\s+`?(\w+)`?', line, re.IGNORECASE)
                func_m = re.match(r'CREATE\s+(?:DEFINER\s*=\s*\S+\s+)?FUNCTION\s+`?(\w+)`?', line, re.IGNORECASE)
                if proc_m:
                    routine_type = 'PROCEDURE'
                    routine_name = proc_m.group(1)
                elif func_m:
                    routine_type = 'FUNCTION'
                    routine_name = func_m.group(1)

                # デリミタ終端を検出
                stripped = line.rstrip('\n').rstrip()
                if stripped.endswith(';;') or stripped.endswith('//'):
                    routine_lines.append(stripped[:-2] + '\n')
                    if routine_type and routine_name:
                        routines.append((routine_type, routine_name, ''.join(routine_lines)))
                    in_routine = False
                    routine_lines = []
                    routine_type = None
                    routine_name = None
                else:
                    routine_lines.append(line)

    return routines


def convert_routine_body(body, routine_type, routine_name, schema):
    """MySQL ストアドプロシージャ/ファンクションを SQL Server 用に変換"""
    result = body

    # DEFINER 削除
    result = re.sub(r'\s*DEFINER\s*=\s*\S+\s*', ' ', result, flags=re.IGNORECASE)

    # バッククォート削除
    result = result.replace('`', '')

    # DELIMITER 削除
    result = re.sub(r'DELIMITER\s+\S+', '', result)

    # MySQL # コメント -> SQL Server -- コメント
    result = re.sub(r'#\s*(.*)$', r'-- \1', result, flags=re.MULTILINE)

    # MySQL COLLATE utf8... 削除
    result = re.sub(r'\s*collate\s+utf8\w*', '', result, flags=re.IGNORECASE)

    # CONCAT('a', b, 'c') -> 'a' + b + 'c'
    def replace_concat(m):
        args_str = m.group(1)
        # 簡易的にカンマで分割（ネストなしの場合）
        args = [a.strip() for a in args_str.split(',')]
        return ' + '.join(args)
    result = re.sub(r'\bCONCAT\(([^)]+)\)', replace_concat, result, flags=re.IGNORECASE)

    # IN/OUT パラメータ名を抽出してから変換
    param_names = []
    for pm in re.finditer(r'\b(?:IN|OUT|INOUT)\s+(\w+)', result, flags=re.IGNORECASE):
        param_names.append(pm.group(1))

    # IN/OUT パラメータ変換: (IN param type) -> (@param type)
    result = re.sub(r'\bIN\s+(\w+)', r'@\1', result, flags=re.IGNORECASE)
    result = re.sub(r'\bOUT\s+(\w+)', r'@\1 OUTPUT', result, flags=re.IGNORECASE)
    result = re.sub(r'\bINOUT\s+(\w+)', r'@\1 OUTPUT', result, flags=re.IGNORECASE)

    # 本文内のパラメータ参照も @付きに変換（既に@が付いていないもの）
    for pname in param_names:
        result = re.sub(r'(?<!@)\b' + re.escape(pname) + r'\b', f'@{pname}', result)

    # 空のパラメータリスト () 削除 (SQL Server では不要)
    result = re.sub(r'(CREATE\s+(?:PROCEDURE|FUNCTION)\s+\S+)\s*\(\s*\)', r'\1', result, flags=re.IGNORECASE)

    # BEGIN -> AS BEGIN (プロシージャ本文の開始)
    result = re.sub(r'^(CREATE\s+(?:PROCEDURE|FUNCTION)\s+[^\n]+)\n\s*BEGIN\b',
                    r'\1\nAS\nBEGIN', result, flags=re.IGNORECASE | re.MULTILINE)

    # IF ... THEN ... END IF -> IF ... BEGIN ... END
    result = re.sub(r'\bTHEN\b', 'BEGIN', result, flags=re.IGNORECASE)
    result = re.sub(r'\bEND\s+IF\b', 'END', result, flags=re.IGNORECASE)
    result = re.sub(r'\bELSEIF\b', 'END ELSE IF', result, flags=re.IGNORECASE)

    # WHILE ... DO ... END WHILE -> WHILE ... BEGIN ... END
    result = re.sub(r'\bDO\b', 'BEGIN', result, flags=re.IGNORECASE)
    result = re.sub(r'\bEND\s+WHILE\b', 'END', result, flags=re.IGNORECASE)

    # 型変換（ルーチン本文内）
    result = re.sub(r'\btinyint\b', 'SMALLINT', result, flags=re.IGNORECASE)
    result = re.sub(r'\bint\(\d+\)', 'INT', result, flags=re.IGNORECASE)
    result = re.sub(r'\bvarchar\((\d+)\)', r'NVARCHAR(\1)', result, flags=re.IGNORECASE)
    result = re.sub(r'\bchar\((\d+)\)', r'NCHAR(\1)', result, flags=re.IGNORECASE)
    result = re.sub(r'\bdatetime\b', 'DATETIME2', result, flags=re.IGNORECASE)
    result = re.sub(r'\btext\b', 'NVARCHAR(MAX)', result, flags=re.IGNORECASE)

    # MySQL のデータベース名.テーブル名 -> スキーマ名.テーブル名
    result = re.sub(r'\bhr01\.(\w+)', rf'{schema}.\1', result)

    # CREATE PROCEDURE/FUNCTION にスキーマ名追加
    result = re.sub(
        r'CREATE\s+(PROCEDURE|FUNCTION)\s+(\w+)',
        rf'CREATE \1 {schema}.\2',
        result,
        flags=re.IGNORECASE
    )

    return result


def write_inserts_streaming(input_path, out, table_name, col_names, schema, batch_size=1000):
    """INSERT 文を行単位でストリーム処理し、変換して書き出す"""
    total_records = 0
    buffer = []  # 現在のバッチバッファ

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.startswith('INSERT INTO'):
                continue

            # INSERT INTO `table` VALUES (...); から VALUES 以降を取得
            m = re.match(r"INSERT INTO `\w+` VALUES (.*);", line.rstrip())
            if not m:
                continue

            tuples = parse_values(m.group(1))
            for t in tuples:
                buffer.append(convert_tuple(t))
                if len(buffer) >= batch_size:
                    out.write(f'INSERT INTO {schema}.{table_name} ({col_names}) VALUES\n')
                    out.write(',\n'.join(buffer))
                    out.write(';\nGO\n\n')
                    total_records += len(buffer)
                    buffer = []

    # 残りのバッファを書き出し
    if buffer:
        out.write(f'INSERT INTO {schema}.{table_name} ({col_names}) VALUES\n')
        out.write(',\n'.join(buffer))
        out.write(';\nGO\n\n')
        total_records += len(buffer)

    return total_records


def convert_file(input_path, output_path, schema='dbo'):
    """MySQL dump ファイルを SQL Server 用に変換"""
    print(f'変換中: {os.path.basename(input_path)}')

    # CREATE TABLE 部分だけ読み取り
    header = extract_create_table_section(input_path)
    table_name, columns, keys, primary_key = parse_create_table(header)

    # ストアドプロシージャ/ファンクション抽出
    routines = extract_routines(input_path)

    # テーブル定義もルーチンもない場合はスキップ
    if not table_name and not routines:
        print(f'  SKIP: 変換対象が見つかりません')
        return False

    with open(output_path, 'w', encoding='utf-8') as out:
        # ヘッダー
        out.write('-- SQL Server conversion of MySQL dump\n')
        out.write(f'-- Original: {os.path.basename(input_path)}\n')
        out.write(f'-- Schema: {schema}\n\n')

        total_records = 0

        # テーブル定義がある場合
        if table_name:
            has_identity = any(c[2] for c in columns)
            col_names = ', '.join(f'[{c[0]}]' for c in columns)

            print(f'  テーブル: {table_name}, カラム: {len(columns)}')

            # DROP TABLE
            out.write(f"IF OBJECT_ID(N'{schema}.{table_name}', N'U') IS NOT NULL\n")
            out.write(f'    DROP TABLE {schema}.{table_name};\nGO\n\n')

            # CREATE TABLE
            out.write(f'CREATE TABLE {schema}.{table_name} (\n')
            col_lines = []
            for col_name, col_def, is_auto in columns:
                if is_auto:
                    # IDENTITY は型名の直後に挿入
                    parts = col_def.split(None, 1)
                    type_name = parts[0]
                    rest = parts[1] if len(parts) > 1 else ''
                    col_lines.append(f'    [{col_name}] {type_name} IDENTITY(1,1) {rest}'.rstrip())
                else:
                    col_lines.append(f'    [{col_name}] {col_def}')
            if primary_key:
                pk_cols = ', '.join(f'[{c}]' for c in primary_key)
                col_lines.append(f'    CONSTRAINT [PK_{table_name}] PRIMARY KEY ({pk_cols})')
            out.write(',\n'.join(col_lines))
            out.write('\n);\nGO\n\n')

            # インデックス
            for key_type, key_name, key_cols in keys:
                cols_str = ', '.join(f'[{c}]' for c in key_cols)
                if key_type == 'UNIQUE':
                    out.write(f'CREATE UNIQUE INDEX [{key_name}] ON {schema}.{table_name} ({cols_str});\n')
                else:
                    out.write(f'CREATE INDEX [{key_name}] ON {schema}.{table_name} ({cols_str});\n')
            if keys:
                out.write('GO\n\n')

            # INSERT データ（ストリーム処理）
            if has_identity:
                out.write(f'SET IDENTITY_INSERT {schema}.{table_name} ON;\nGO\n\n')

            total_records = write_inserts_streaming(input_path, out, table_name, col_names, schema)

            if has_identity and total_records > 0:
                out.write(f'SET IDENTITY_INSERT {schema}.{table_name} OFF;\nGO\n\n')

        # ストアドプロシージャ/ファンクション
        if routines:
            out.write('-- =============================================\n')
            out.write('-- Stored Procedures / Functions\n')
            out.write('-- =============================================\n\n')
            for rtype, rname, rbody in routines:
                out.write(f'-- {rtype}: {rname}\n')
                out.write(f"IF OBJECT_ID(N'{schema}.{rname}', N'{'P' if rtype == 'PROCEDURE' else 'FN'}') IS NOT NULL\n")
                out.write(f'    DROP {rtype} {schema}.{rname};\nGO\n\n')
                converted_body = convert_routine_body(rbody, rtype, rname, schema)
                out.write(converted_body)
                out.write('\nGO\n\n')

    if table_name:
        print(f'  レコード: {total_records}')
    if routines:
        print(f'  ルーチン: {len(routines)} ({", ".join(r[1] for r in routines)})')
    print(f'  出力: {output_path}')
    return True


def generate_sqlcmd_file(output_path, sql_files, server, user, password, database):
    """sqlcmd で CUI 実行するためのバッチファイルを出力"""
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write('@echo off\n')
        out.write('REM sqlcmd batch execution script\n')
        out.write(f'REM Server: {server}\n')
        out.write(f'REM Database: {database}\n')
        out.write(f'REM Generated by convert_mysql_to_mssql.py\n\n')

        for sql_file in sql_files:
            basename = os.path.basename(sql_file)
            out.write(f'echo Executing {basename}...\n')
            out.write(f'sqlcmd -S {server} -U {user} -P {password} -d {database} -i "{sql_file}" -f 65001\n')
            out.write('if %ERRORLEVEL% NEQ 0 (\n')
            out.write(f'    echo ERROR: {basename} failed.\n')
            out.write('    exit /b %ERRORLEVEL%\n')
            out.write(')\n')
            out.write(f'echo {basename} completed.\n\n')

        out.write('echo All files executed successfully.\n')

    print(f'sqlcmd 実行ファイル: {output_path}')


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # hr01/
    default_input = os.path.join(base_dir, 'mysql')
    default_output = os.path.join(base_dir, 'mssql')

    parser = argparse.ArgumentParser(description='MySQL dump ファイルを SQL Server 用に変換')
    parser.add_argument('files', nargs='*', help='変換対象ファイル名 (省略時は入力ディレクトリ内の全 *.sql)')
    parser.add_argument('-i', '--input-dir', default=default_input,
                        help=f'入力ディレクトリパス (デフォルト: {default_input})')
    parser.add_argument('-o', '--output-dir', default=default_output,
                        help=f'出力ディレクトリパス (デフォルト: {default_output})')
    parser.add_argument('--schema', default='dbo',
                        help='出力SQLのスキーマ名 (デフォルト: dbo)')
    parser.add_argument('--sqlcmd', action='store_true',
                        help='sqlcmd実行用バッチファイルも出力する')
    parser.add_argument('--server', default='127.0.0.1',
                        help='SQL Server ホスト (デフォルト: 127.0.0.1)')
    parser.add_argument('--user', default='mochi',
                        help='SQL Server ユーザ名 (デフォルト: mochi)')
    parser.add_argument('--password', default='bell0100',
                        help='SQL Server パスワード (デフォルト: bell0100)')
    parser.add_argument('--database', default='hr01',
                        help='SQL Server データベース名 (デフォルト: hr01)')
    args = parser.parse_args()

    mysql_dir = os.path.abspath(args.input_dir)
    mssql_dir = os.path.abspath(args.output_dir)

    os.makedirs(mssql_dir, exist_ok=True)

    # 引数で対象ファイルを指定、なければ全ファイル
    if args.files:
        files = []
        for arg in args.files:
            path = os.path.join(mysql_dir, arg) if not os.path.isabs(arg) else arg
            if os.path.exists(path):
                files.append(path)
            else:
                print(f'ファイルが見つかりません: {path}')
    else:
        files = sorted(glob.glob(os.path.join(mysql_dir, '*.sql')))

    if not files:
        print('変換対象のファイルがありません')
        sys.exit(1)

    print(f'変換対象: {len(files)} ファイル')
    print(f'スキーマ: {args.schema}\n')

    success = 0
    output_files = []
    for input_path in files:
        basename = os.path.basename(input_path)
        output_path = os.path.join(mssql_dir, basename)
        if convert_file(input_path, output_path, schema=args.schema):
            success += 1
            output_files.append(output_path)
        print()

    print(f'完了: {success}/{len(files)} ファイル変換')

    # sqlcmd 実行用バッチファイル出力
    if args.sqlcmd and output_files:
        sqlcmd_path = os.path.join(mssql_dir, 'exec_sqlcmd.bat')
        generate_sqlcmd_file(sqlcmd_path, output_files,
                            args.server, args.user, args.password, args.database)


if __name__ == '__main__':
    main()
