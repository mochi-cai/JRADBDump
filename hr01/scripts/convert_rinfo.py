import re
import sys
import argparse

parser = argparse.ArgumentParser(description='MySQL dump (rinfo) を SQL Server 用に変換')
parser.add_argument('input', help='入力ファイルパス (MySQL dump)')
parser.add_argument('output', help='出力ファイルパス (SQL Server SQL)')
args = parser.parse_args()

with open(args.input, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the INSERT values
m = re.search(r"INSERT INTO `rinfo` VALUES (.*?);", content, re.DOTALL)
if not m:
    print('No INSERT found')
    sys.exit(1)

values_str = m.group(1)

# Parse individual value tuples
tuples = []
i = 0
while i < len(values_str):
    if values_str[i] == '(':
        j = i + 1
        in_quote = False
        while j < len(values_str):
            c = values_str[j]
            if c == "'" and values_str[j-1] != '\\':
                in_quote = not in_quote
            elif c == ')' and not in_quote:
                tuples.append(values_str[i:j+1])
                i = j + 1
                break
            j += 1
        else:
            i = j
    else:
        i += 1

print(f'Found {len(tuples)} records')

with open(args.output, 'w', encoding='utf-8') as out:
    out.write('-- SQL Server conversion of MySQL dump\n')
    out.write('-- Original: hr01_rinfo.sql\n')
    out.write('-- Database: hr01\n\n')
    out.write("IF OBJECT_ID(N'dbo.rinfo', N'U') IS NOT NULL\n")
    out.write('    DROP TABLE dbo.rinfo;\nGO\n\n')
    out.write('CREATE TABLE dbo.rinfo (\n')
    out.write('    [idx] INT IDENTITY(1,1) NOT NULL,\n')
    out.write('    [rdate] DATE NULL,\n')
    out.write('    [rplace] NVARCHAR(20) NULL,\n')
    out.write('    [rctype] NVARCHAR(8) NULL,\n')
    out.write('    [rcourse] NVARCHAR(8) NULL,\n')
    out.write('    [rlength] SMALLINT NULL,\n')
    out.write('    [rcond] NCHAR(8) NULL,\n')
    out.write('    [rwether] NCHAR(8) NULL,\n')
    out.write('    [rno] SMALLINT NULL,\n')
    out.write('    [rname] NVARCHAR(100) NULL,\n')
    out.write('    [rnoe] SMALLINT NULL\n')
    out.write(');\nGO\n\n')
    out.write('CREATE UNIQUE INDEX [UQ_race] ON dbo.rinfo ([rdate], [rplace], [rno]);\nGO\n\n')
    out.write('CREATE INDEX [IX_rinfo_idx] ON dbo.rinfo ([idx]);\nGO\n\n')
    out.write('SET IDENTITY_INSERT dbo.rinfo ON;\nGO\n\n')

    batch_size = 1000
    columns = '[idx], [rdate], [rplace], [rctype], [rcourse], [rlength], [rcond], [rwether], [rno], [rname], [rnoe]'

    for batch_start in range(0, len(tuples), batch_size):
        batch = tuples[batch_start:batch_start+batch_size]
        out.write(f'INSERT INTO dbo.rinfo ({columns}) VALUES\n')

        converted = []
        for t in batch:
            inner = t[1:-1]
            vals = []
            ci = 0
            current = ''
            in_q = False
            while ci < len(inner):
                ch = inner[ci]
                if ch == "'" and (ci == 0 or inner[ci-1] != '\\'):
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

            converted.append('(' + ', '.join(new_vals) + ')')

        out.write(',\n'.join(converted))
        out.write(';\nGO\n\n')

    out.write('SET IDENTITY_INSERT dbo.rinfo OFF;\nGO\n')

print('Done')
