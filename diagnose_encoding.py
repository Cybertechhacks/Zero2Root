"""
Diagnose the exact bytes around a known-bad pattern.
"""
with open(r'd:/pentestvault-final (2)/pentestvault-final/pentestvault/site/index.html', 'rb') as f:
    content = f.read()

# Find "Level 0" and show the next 40 bytes
idx = content.find(b'Level 0')
if idx >= 0:
    segment = content[idx:idx+40]
    print("Bytes:", segment.hex(' '))
    print("Text (utf-8 decode, errors=replace):", segment.decode('utf-8', errors='replace'))
    print("Text (latin-1 decode):", segment.decode('latin-1'))
