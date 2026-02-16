---
description: How to set up, run, and test the Whisk Desktop PySide6 application
---

# Run Whisk Desktop App

## Prerequisites

- Python 3.9+
- macOS (primary) / Windows (supported)

## Steps

// turbo-all

1. **Install dependencies**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pip install -r requirements.txt
```

2. **Run the application**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 main.py
```

3. **Run unit tests**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/ -v --tb=short
```

4. **Run a specific test file**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/test_theme_manager.py -v
```

5. **Run tests with coverage**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/ -v --cov=app --cov-report=term-missing
```

## Quick Verification

After launching, verify:

- Config panel loads with saved settings (QSettings persistence)
- Light/dark theme toggle works
- Language switch (EN/VI) updates all labels
- Add reference images via dynamic slots (up to 5 per category)
- Add to Queue creates rows with correct images_per_prompt output placeholders
- Running tasks show animated pulsing progress bars
- Reset button clears all config to defaults
