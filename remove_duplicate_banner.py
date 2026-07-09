"""
Remove the duplicate old admonition.tip 'How to Use This Guide' block from index.html.
Keep the new pv-onboarding-banner, remove the old MkDocs admonition.
"""
import re

with open(r'd:/pentestvault-final (2)/pentestvault-final/pentestvault/site/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the old admonition.tip block entirely
# Pattern: <div class="admonition tip">...</div> containing "How to Use This Guide"
pattern = r'<div class="admonition tip">\s*<p class="admonition-title">How to Use This Guide</p>.*?</div>\s*<hr\s*/>'
content_new = re.sub(pattern, '<hr />', content, count=1, flags=re.DOTALL)

if content_new == content:
    print("Pattern not matched - trying fallback")
    # Fallback: remove just the admonition div
    pattern2 = r'<div class="admonition tip">\s*<p class="admonition-title">How to Use This Guide</p>.*?</div>'
    content_new = re.sub(pattern2, '', content, count=1, flags=re.DOTALL)

with open(r'd:/pentestvault-final (2)/pentestvault-final/pentestvault/site/index.html', 'w', encoding='utf-8') as f:
    f.write(content_new)

# Verify
remaining = content_new.count('How to Use This Guide')
print(f'Done. Remaining "How to Use This Guide" occurrences: {remaining}')
