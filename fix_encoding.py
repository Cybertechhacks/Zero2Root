"""
Fix: Remove the rogue right-double-quote (U+201D = e2 80 9d) that follows em-dashes 
in card titles. Pattern: "Level X —" Foo" should be "Level X — Foo"
"""
import glob

files = glob.glob(r'd:/pentestvault-final (2)/pentestvault-final/pentestvault/site/**/*.html', recursive=True)

# em-dash followed immediately by right-double-quote then a space
em_dash = b'\xe2\x80\x94'
rdquote = b'\xe2\x80\x9d'
space = b' '

fixed_total = 0
for filepath in files:
    with open(filepath, 'rb') as f:
        content = f.read()
    
    original = content
    # Remove the right-double-quote when it directly follows an em-dash + space pattern
    content = content.replace(em_dash + rdquote + space, em_dash + space)
    # Also handle em-dash + rdquote at end of a word (no space after)
    content = content.replace(em_dash + rdquote, em_dash)
    
    if content != original:
        with open(filepath, 'wb') as f:
            f.write(content)
        count = original.count(em_dash + rdquote)
        fixed_total += count
        print(f'Fixed {count} occurrences in: {filepath}')

print(f'Total fixed: {fixed_total}')
