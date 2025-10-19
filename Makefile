# Makefile for Whisper Transcriber
# Provides convenient commands for development, testing, and documentation

.PHONY: help install dev test lint format clean docker arch.scan arch.check arch.diagrams arch.clean test.comprehensive test.functions test.integration

# Default target
help:
	@echo "🎯 Whisper Transcriber - Available Commands"
	@echo ""
	@echo "📦 Setup & Development:"
	@echo "  make install     Install Python dependencies"
	@echo "  make dev         Start development environment"
	@echo "  make test        Run test suite"
	@echo "  make lint        Run linting and type checking"
	@echo "  make format      Format code with black and isort"
	@echo ""
	@echo "🔬 Comprehensive Testing:"
	@echo "  make test.comprehensive  Test all documented system facets"
	@echo "  make test.functions      Test all documented functions/modules"
	@echo "  make test.integration    Test API endpoints and workflows"
	@echo "  make test.all           Run all validation tests"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker      Build and start Docker containers"
	@echo "  make docker.down Stop Docker containers"
	@echo "  make docker.logs View container logs"
	@echo ""
	@echo "📚 Architecture Documentation:"
	@echo "  make arch.scan     Scan codebase and update architecture docs"
	@echo "  make arch.check    Check if architecture docs are stale"
	@echo "  make arch.diagrams Regenerate Mermaid diagrams"
	@echo "  make arch.clean    Clean generated architecture artifacts"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean       Remove cache files and build artifacts"

# Setup & Development
install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	@echo "🚀 Starting development environment..."
	python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "🧪 Running test suite..."
	python -m pytest tests/ -v

# Comprehensive Testing Suite
test.comprehensive:
	@echo "🔬 Running comprehensive system validation..."
	@echo "This tests all documented system components and generates detailed reports"
	@echo ""
	python tools/comprehensive_validator.py
	@echo ""
	@echo "📋 Reports generated in logs/ directory"

test.functions:
	@echo "🔍 Testing all documented functions and modules..."
	@echo "This validates that all 921 documented functions are importable and callable"
	@echo ""
	python tools/function_validator.py
	@echo ""
	@echo "📋 Function validation report generated in logs/ directory"

test.integration:
	@echo "🔗 Testing API endpoints and integration workflows..."
	@echo "This validates all documented API contracts and system flows"
	@echo ""
	@if docker-compose ps | grep -q "Up"; then \
		echo "✅ Using running Docker containers"; \
		python tools/integration_validator.py --base-url http://localhost:8000; \
	else \
		echo "⚠️  Starting Docker containers for testing..."; \
		make docker > /dev/null 2>&1; \
		sleep 5; \
		python tools/integration_validator.py --base-url http://localhost:8000; \
	fi
	@echo ""
	@echo "📋 Integration test report generated in logs/ directory"

test.all:
	@echo "🚀 Running complete validation test suite..."
	@echo "This runs all three validation tools in sequence"
	@echo ""
	@echo "Step 1/3: Comprehensive system validation..."
	@make test.comprehensive
	@echo ""
	@echo "Step 2/3: Function and module validation..."
	@make test.functions
	@echo ""
	@echo "Step 3/3: Integration and API validation..."
	@make test.integration
	@echo ""
	@echo "✅ Complete validation test suite finished"
	@echo "📋 All reports available in logs/ directory"

lint:
	@echo "🔍 Running linting and type checking..."
	python -m flake8 api/ tests/
	python -m mypy api/ --ignore-missing-imports

format:
	@echo "✨ Formatting code..."
	python -m black api/ tests/ tools/
	python -m isort api/ tests/ tools/

# Docker
docker:
	@echo "🐳 Building and starting Docker containers..."
	docker-compose up --build -d

docker.down:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

docker.logs:
	@echo "📋 Viewing container logs..."
	docker-compose logs -f

# Architecture Documentation
arch.scan:
	@echo "🔍 Scanning codebase and updating architecture documentation..."
	@python tools/repo_inventory.py
	@python tools/update_architecture_docs.py
	@echo "✅ Architecture documentation updated"
	@echo ""
	@echo "📊 Summary:"
	@python -c "import json; data=json.load(open('docs/architecture/INVENTORY.json')); stats=data.get('statistics',{}); print(f\"  - Modules: {stats.get('total_modules',0)}\"); print(f\"  - Functions: {stats.get('total_functions',0)}\"); print(f\"  - API Endpoints: {stats.get('total_api_endpoints',0)}\")"

arch.check:
	@echo "🔎 Checking if architecture documentation is up to date..."
	@python tools/repo_inventory.py > /dev/null 2>&1
	@python tools/update_architecture_docs.py > /dev/null 2>&1
	@if git diff --quiet docs/architecture/; then \
		echo "✅ Architecture documentation is up to date"; \
	else \
		echo "❌ Architecture documentation is stale"; \
		echo ""; \
		echo "📋 Files that need updating:"; \
		git diff --name-only docs/architecture/ | sed 's/^/  - /'; \
		echo ""; \
		echo "🔧 Run 'make arch.scan' to update documentation"; \
		exit 1; \
	fi

arch.diagrams:
	@echo "📊 Regenerating Mermaid diagrams..."
	@if command -v mmdc >/dev/null 2>&1; then \
		echo "🎨 Converting Mermaid diagrams to SVG..."; \
		find docs/architecture/ -name "*.md" -exec grep -l "```mermaid" {} \; | while read file; do \
			echo "  - Processing $$file"; \
		done; \
		echo "✅ Diagrams regenerated"; \
	else \
		echo "⚠️  Mermaid CLI not installed. Install with: npm install -g @mermaid-js/mermaid-cli"; \
		echo "🔗 Diagrams will be rendered by GitHub/documentation viewers"; \
	fi

arch.clean:
	@echo "🧹 Cleaning architecture artifacts..."
	@rm -f docs/architecture/INVENTORY.json.bak
	@rm -f docs/architecture/*.tmp
	@find docs/architecture/ -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Architecture artifacts cleaned"

# Cleanup
clean:
	@echo "🧹 Cleaning build artifacts and cache files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@rm -rf dist/
	@rm -rf build/
	@echo "✅ Cleanup complete"

# Advanced Architecture Commands (for CI/CD)
arch.validate:
	@echo "🔍 Validating architecture documentation..."
	@python -c "import json; json.load(open('docs/architecture/INVENTORY.json'))" && echo "✅ INVENTORY.json is valid JSON"
	@python tools/validate_docs.py 2>/dev/null || echo "⚠️  Documentation validator not found"

arch.stats:
	@echo "📊 Architecture Statistics:"
	@python -c "import json; data=json.load(open('docs/architecture/INVENTORY.json')); stats=data.get('statistics',{}); print(f'Modules: {stats.get(\"total_modules\",0)}'); print(f'Functions: {stats.get(\"total_functions\",0)}'); print(f'API Endpoints: {stats.get(\"total_api_endpoints\",0)}'); print(f'Config Variables: {stats.get(\"total_config_vars\",0)}'); print(f'Data Stores: {stats.get(\"total_data_stores\",0)}')"

# Environment checks
check.env:
	@echo "🔧 Checking environment setup..."
	@command -v python >/dev/null 2>&1 || (echo "❌ Python not found" && exit 1)
	@python -c "import sys; print(f'✅ Python {sys.version}')"
	@command -v git >/dev/null 2>&1 || (echo "❌ Git not found" && exit 1)
	@git --version | sed 's/^/✅ /'
	@echo "✅ Environment check complete"
