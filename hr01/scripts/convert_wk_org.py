import re
import sys
import argparse

parser = argparse.ArgumentParser(description='MySQL dump (wk_org) を SQL Server 用に変換')
parser.add_argument('input', help='入力ファイルパス (MySQL dump)')
parser.add_argument('output', help='出力ファイルパス (SQL Server SQL)')
args = parser.parse_args()

with open(args.input, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the INSERT values
m = re.search(r"INSERT INTO `wk_org` VALUES (.*?);", content, re.DOTALL)
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
            if c == "'" :
                if j > 0 and values_str[j-1] == '\\' and not (j > 1 and values_str[j-2] == '\\'):
                    pass  # escaped quote, skip
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
    out.write('-- Original: hr01_wk_org.sql\n')
    out.write('-- Database: hr01\n\n')
    out.write("IF OBJECT_ID(N'dbo.wk_org', N'U') IS NOT NULL\n")
    out.write('    DROP TABLE dbo.wk_org;\nGO\n\n')
    out.write('CREATE TABLE dbo.wk_org (\n')
    out.write('    [idx] INT IDENTITY(1,1) NOT NULL,\n')
    out.write('    [rdate] DATE NULL,\n')
    out.write('    [rplace] NVARCHAR(20) NULL,\n')
    out.write('    [rno] SMALLINT NULL,\n')
    out.write('    [rname] NVARCHAR(100) NULL,\n')
    out.write('    [rctype] NVARCHAR(8) NULL,\n')
    out.write('    [rcourse] NVARCHAR(8) NULL,\n')
    out.write('    [rlength] SMALLINT NULL,\n')
    out.write('    [rshukai] NVARCHAR(4) NULL,\n')
    out.write('    [rcond] NCHAR(8) NULL,\n')
    out.write('    [rwether] NCHAR(8) NULL,\n')
    out.write('    [hname] NVARCHAR(20) NULL,\n')
    out.write('    [jname] NVARCHAR(256) NULL,\n')
    out.write('    [rwakuno] SMALLINT NULL,\n')
    out.write('    [rumano] SMALLINT NULL,\n')
    out.write('    [rresult] SMALLINT NULL,\n')
    out.write('    [rnoresult] NCHAR(8) NULL,\n')
    out.write('    [rninki] SMALLINT NULL,\n')
    out.write('    [rodds] DECIMAL(5,1) NULL,\n')
    out.write('    [hsei] NVARCHAR(4) NULL,\n')
    out.write('    [hrei] SMALLINT NULL,\n')
    out.write('    [hwt] SMALLINT NULL,\n')
    out.write('    [hwtbfsa] SMALLINT NULL,\n')
    out.write('    [hkinryo] DECIMAL(3,1) NULL,\n')
    out.write('    [rtime] TIME(3) NULL,\n')
    out.write('    [rtyakusa] NVARCHAR(256) NULL,\n')
    out.write('    [r3f] FLOAT NULL,\n')
    out.write('    [rbante] NVARCHAR(256) NULL,\n')
    out.write('    [rpace] NVARCHAR(256) NULL,\n')
    out.write('    [rlap1] NVARCHAR(256) NULL,\n')
    out.write('    [rlap2] NVARCHAR(256) NULL,\n')
    out.write('    [rtrecen] NVARCHAR(256) NULL,\n')
    out.write('    [rkyusha] NVARCHAR(256) NULL,\n')
    out.write('    [rowner] NVARCHAR(256) NULL,\n')
    out.write('    [hname_cd] NVARCHAR(256) NULL,\n')
    out.write('    [jname_cd] NVARCHAR(256) NULL,\n')
    out.write('    [rkyusha_cd] NVARCHAR(256) NULL,\n')
    out.write('    [rowner_cd] NVARCHAR(256) NULL,\n')
    out.write("    [delflg] NCHAR(2) NULL DEFAULT '00',\n")
    out.write('    CONSTRAINT [PK_wk_org] PRIMARY KEY ([idx])\n')
    out.write(');\nGO\n\n')
    out.write('CREATE INDEX [idx_rdate] ON dbo.wk_org ([rdate]);\n')
    out.write('CREATE INDEX [idx_rname] ON dbo.wk_org ([rname]);\n')
    out.write('CREATE INDEX [idx_hname] ON dbo.wk_org ([hname]);\n')
    out.write('CREATE INDEX [idx_jname] ON dbo.wk_org ([jname]);\n')
    out.write('CREATE INDEX [idx_rplace] ON dbo.wk_org ([rplace]);\n')
    out.write('CREATE INDEX [idx_date_place_rno] ON dbo.wk_org ([rdate], [rplace], [rno]);\n')
    out.write('CREATE INDEX [idx_rkyusha] ON dbo.wk_org ([rkyusha]);\n')
    out.write('CREATE INDEX [idx_hname_cd] ON dbo.wk_org ([hname_cd]);\n')
    out.write('CREATE INDEX [idx_jname_cd] ON dbo.wk_org ([jname_cd]);\n')
    out.write('CREATE INDEX [idx_rkyusha_cd] ON dbo.wk_org ([rkyusha_cd]);\n')
    out.write('CREATE INDEX [idx_rowner_cd] ON dbo.wk_org ([rowner_cd]);\n')
    out.write('GO\n\n')
    out.write('SET IDENTITY_INSERT dbo.wk_org ON;\nGO\n\n')

    batch_size = 1000
    columns = '[idx], [rdate], [rplace], [rno], [rname], [rctype], [rcourse], [rlength], [rshukai], [rcond], [rwether], [hname], [jname], [rwakuno], [rumano], [rresult], [rnoresult], [rninki], [rodds], [hsei], [hrei], [hwt], [hwtbfsa], [hkinryo], [rtime], [rtyakusa], [r3f], [rbante], [rpace], [rlap1], [rlap2], [rtrecen], [rkyusha], [rowner], [hname_cd], [jname_cd], [rkyusha_cd], [rowner_cd], [delflg]'

    for batch_start in range(0, len(tuples), batch_size):
        batch = tuples[batch_start:batch_start+batch_size]
        out.write(f'INSERT INTO dbo.wk_org ({columns}) VALUES\n')

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
                    current += "''"
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

            converted.append('(' + ', '.join(new_vals) + ')')

        out.write(',\n'.join(converted))
        out.write(';\nGO\n\n')

    out.write('SET IDENTITY_INSERT dbo.wk_org OFF;\nGO\n')

print('Done')
