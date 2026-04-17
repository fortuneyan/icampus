#!/usr/bin/env python
import sys

sys.path.insert(0, "C:/workspace/AI_school/smart-campus/backend")

try:
    from app.main import app

    print("SUCCESS: Backend OK")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
