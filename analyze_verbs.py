"""Quick script to analyze strong verbs in the generated resume."""
import re

# Read the latest LaTeX file
with open('outputs/latex/resume_20260123_234000.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all resumeItem bullets
bullets = re.findall(r'\\resumeItem\{([^}]+)\}', content)

# Extract first word (verb) from each bullet
verbs = []
for bullet in bullets:
    if bullet.strip():
        first_word = bullet.split()[0]
        verbs.append(first_word)

print("="*60)
print("STRONG VERBS ANALYSIS")
print("="*60)
print("\nVerbs used in resume:")
for i, verb in enumerate(verbs, 1):
    print(f"{i:2d}. {verb}")

print(f"\n{'='*60}")
print(f"Total bullets: {len(verbs)}")
print(f"Unique verbs: {len(set(verbs))}")
print(f"Duplicates: {len(verbs) - len(set(verbs))}")

# Check for mandatory verbs
print(f"\n{'='*60}")
print("MANDATORY VERBS CHECK:")
print(f"  ✓ Engineered: {'YES' if 'Engineered' in verbs else 'NO'}")
print(f"  ✓ Architected: {'YES' if 'Architected' in verbs else 'NO'}")

# Find any duplicates
from collections import Counter
verb_counts = Counter(verbs)
duplicates = {v: c for v, c in verb_counts.items() if c > 1}

if duplicates:
    print(f"\n{'='*60}")
    print("WARNING: Duplicate verbs found:")
    for verb, count in duplicates.items():
        print(f"  - {verb}: {count} times")
else:
    print(f"\n{'='*60}")
    print("✓ NO DUPLICATES FOUND - All verbs are unique!")

print(f"{'='*60}\n")
