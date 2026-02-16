---
description: Run test suite with coverage report and identify low-coverage modules
---

# Test Coverage Report

## Steps

// turbo-all

1. **Run full test suite with coverage**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/ --cov=app --cov-report=term-missing -q
```

2. **Show only modules below 80% coverage**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/ --cov=app --cov-report=term-missing -q 2>&1 | grep -E '^\S.*\s+[0-7][0-9]%|^\S.*\s+0%' | sort -t'%' -k1 -n
```

3. **Count total tests**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/ --co -q 2>&1 | tail -1
```

## Reading Results

- Focus on modules with **< 80%** coverage
- Prioritize modules with high statement count AND low coverage
- Modules at 0% need new test files in `tests/test_<module>.py`
- Check `conftest.py` for shared fixtures before creating new ones
