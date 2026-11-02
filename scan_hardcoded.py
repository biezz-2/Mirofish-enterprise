import os
import re

cjk_pattern = re.compile(r'[\u4e00-\u9fff]')

results = []

for root, dirs, files in os.walk('frontend/src'):
    for f in files:
        if f.endswith('.vue'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            in_template = False
            in_script = False
            in_style = False
            
            file_matches = []
            for idx, line in enumerate(lines, 1):
                clean = line.strip()
                if '<template' in clean:
                    in_template = True
                if '</template>' in clean:
                    in_template = False
                if '<script' in clean:
                    in_script = True
                if '</script>' in clean:
                    in_script = False
                if '<style' in clean:
                    in_style = True
                if '</style>' in clean:
                    in_style = False
                
                # Check for CJK in template or script, ignoring pure comments
                if cjk_pattern.search(line):
                    # check if pure comment
                    is_comment = False
                    if in_template:
                        if clean.startswith('<!--') and clean.endswith('-->'):
                            is_comment = True
                    elif in_script:
                        if clean.startswith('//') or clean.startswith('/*') or clean.startswith('*'):
                            is_comment = True
                    elif in_style:
                        is_comment = True
                    
                    if not is_comment:
                        file_matches.append((idx, in_template, in_script, in_style, clean))
            
            if file_matches:
                results.append((path, file_matches))

total_hardcoded = sum(len(m) for _, m in results)
print(f"Total hardcoded lines: {total_hardcoded} across {len(results)} Vue files")
for path, matches in results:
    print(f"\n{path} ({len(matches)} lines):")
    for idx, in_t, in_s, in_sty, txt in matches[:5]:
        loc = 'template' if in_t else ('script' if in_s else ('style' if in_sty else 'other'))
        print(f"  L{idx} [{loc}]: {txt[:80]}")
    if len(matches) > 5:
        print(f"  ... and {len(matches)-5} more")
