#!/usr/bin/env python3
"""Fix mojibake encoding in dashboard.html caused by PowerShell Set-Content."""
import codecs

# The file was originally UTF-8, read by PowerShell as Windows-1252,
# then written back as UTF-8. Each UTF-8 multi-byte char became multiple Latin-1 chars.
# Fix: read file, re-encode each char sequence as its original Unicode codepoint.

def fix_mojibake(text):
    """Decode text that was encoded as UTF-8, read as Latin-1, stored as UTF-8 again."""
    # Encode back to bytes treating as latin-1, then decode as UTF-8
    try:
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text

def fix_file(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # Fix line by line to handle partial mojibake
    lines = content.split('\n')
    fixed_lines = []
    fixes = 0
    for line in lines:
        try:
            fixed = line.encode('latin-1').decode('utf-8')
            if fixed != line:
                fixes += 1
            fixed_lines.append(fixed)
        except (UnicodeDecodeError, UnicodeEncodeError):
            fixed_lines.append(line)  # keep as-is if can't fix

    fixed_content = '\n'.join(fixed_lines)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"Fixed {fixes} lines in {path}")

if __name__ == '__main__':
    fix_file('app/templates/admin/dashboard.html')
