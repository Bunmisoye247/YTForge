from __future__ import annotations

import os

os.environ.setdefault("YTFORGE_APP_ENV", "development")
os.environ.setdefault("DATABASE_PASSWORD", "test-password")
os.environ.setdefault("JWT_SECRET", "test-secret")
