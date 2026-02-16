.PHONY: install run test test-cov build-mac build-win clean

install:
	python3 -m pip install -r requirements.txt

run:
	python3 main.py

test:
	python3 -m pytest tests/ -v --tb=short

test-cov:
	python3 -m pytest tests/ -v --cov=app --cov-report=term-missing

build-mac:
	chmod +x scripts/build_mac.sh && ./scripts/build_mac.sh

build-win:
	scripts/build_win.bat

clean:
	rm -rf build/ dist/ __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
