import re
import sys
import argparse

parser = argparse.ArgumentParser(description='MySQL dump (hinfo) を SQL Server 用に変換')
parser.add_argument('input', help='入力ファイルパス (MySQL dump)')
parser.add_argument('output', help='出力ファイルパス (SQL Server SQL)')
args = parser.parse_args()

with open(args.input, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract CREATE TABLE to find all keys
ct_match = re.search(r'CREATE TABLE `hinfo` \((.*?)\) ENGINE=', content, re.DOTALL)
if ct_match:
    print("CREATE TABLE columns found")
    print(ct_match.group(1)[:500])

# Extract the INSERT values
m = re.search(r"INSERT INTO `hinfo` VALUES (.*?);", content, re.DOTALL)
if not m:
    print('No INSERT found')
    sys.exit(1)

values_str = m.group(1)

# Parse individual value tuples - handle escaped quotes (\')
tuples = []
i = 0
while i < len(values_str):
    if values_str[i] == '(':
        j = i + 1
        in_quote = False
        while j < len(values_str):
            c = values_str[j]
            if c == "'" and values_str[j-1:j] != '\\':
                # Check for double backslash (\\') which means actual backslash + start/end quote
                if j >= 2 and values_str[j-2:j] == '\\\\':
                    in_quote = not in_quote
                else:
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
    out.write('-- Original: hr01_hinfo.sql\n')
    out.write('-- Database: hr01\n\n')
    out.write("IF OBJECT_ID(N'dbo.hinfo', N'U') IS NOT NULL\n")
    out.write('    DROP TABLE dbo.hinfo;\nGO\n\n')
    out.write('CREATE TABLE dbo.hinfo (\n')
    out.write('    [hname_cd] NVARCHAR(256) NOT NULL,\n')
    out.write('    [hname] NVARCHAR(20) NOT NULL,\n')
    out.write('    [f] NVARCHAR(256) NULL,\n')
    out.write('    [m] NVARCHAR(256) NULL,\n')
    out.write('    [ff] NVARCHAR(256) NULL,\n')
    out.write('    [fm] NVARCHAR(256) NULL,\n')
    out.write('    [mf] NVARCHAR(256) NULL,\n')
    out.write('    [mm] NVARCHAR(256) NULL,\n')
    out.write("    [del_flg] NCHAR(2) NOT NULL DEFAULT '00',\n")
    out.write('    CONSTRAINT [PK_hinfo] PRIMARY KEY ([hname_cd])\n')
    out.write(');\nGO\n\n')
    out.write('CREATE UNIQUE INDEX [hname_cd_UNIQUE] ON dbo.hinfo ([hname_cd]);\nGO\n\n')

    batch_size = 1000
    columns = '[hname_cd], [hname], [f], [m], [ff], [fm], [mf], [mm], [del_flg]'

    for batch_start in range(0, len(tuples), batch_size):
        batch = tuples[batch_start:batch_start+batch_size]
        out.write(f'INSERT INTO dbo.hinfo ({columns}) VALUES\n')

        converted = []
        for t in batch:
            inner = t[1:-1]
            vals = []
            ci = 0
            current = ''
            in_q = False
            while ci < len(inner):
                ch = inner[ci]
                if ch == '\\' and ci + 1 < len(inner) and inner[ci+1] == "'":
                    # MySQL escaped quote \' -> SQL Server doubled quote ''
                    current += "''"
                    ci += 2
                    continue
                elif ch == "'" and not (ci > 0 and inner[ci-1] == '\\'):
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

print('Done')
