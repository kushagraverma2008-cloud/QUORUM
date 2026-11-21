import os
import re

SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"(?i)(?:api_key|apikey|secret|password|token)\s*[:=]\s*['\"][0-9a-zA-Z\-_]{16,}['\"]"),
    re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),
]

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".cache"}
EXCLUDE_FILES = {".env"}  # .env is explicitly gitignored

violations = []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for file in files:
        if file in EXCLUDE_FILES or file.endswith((".pyc", ".png", ".jpg", ".ico", ".woff2", ".ttf")):
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pattern in SECRET_PATTERNS:
                    matches = pattern.findall(content)
                    if matches:
                        violations.append((filepath, len(matches)))
        except Exception:
            pass

if violations:
    print("WARNING: Secrets detected:")
    for f, count in violations:
        print(f"  {f}: {count} occurrences")
    exit(1)
else:
    print("SECRET SCAN CLEAN: Zero leaked keys or secrets found in codebase.")
    exit(0)

