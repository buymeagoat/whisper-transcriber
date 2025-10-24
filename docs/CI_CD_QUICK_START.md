# CI/CD Pipeline Quick Start Guide

## 🚀 Getting Started with CI/CD

The Whisper Transcriber project includes a **comprehensive, automated CI/CD pipeline** that handles testing, security scanning, building, and deployment. This guide helps developers understand how to work with the pipeline effectively.

## 🔄 Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... develop your feature ...

# Commit and push
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 2. Pull Request Process
When you create a PR, the pipeline automatically:

✅ **Code Quality Checks**
- Runs linting (black, flake8, eslint)
- Validates formatting and style
- Performs type checking (mypy)

✅ **Security Scanning**
- Scans for vulnerabilities (bandit, safety)
- Validates dependencies
- Checks for security issues

✅ **Comprehensive Testing**
- Backend tests with pytest
- Frontend tests with Jest
- Integration tests
- Build validation

✅ **Build Verification**
- Docker container builds
- Multi-platform compatibility
- Artifact generation

### 3. Staging Deployment (Automatic)
Once merged to `main`:
- Automatic deployment to staging environment
- E2E tests with Playwright
- Performance testing with load validation
- Smoke tests on staging

### 4. Production Release
```bash
# Create release tag
git tag v1.0.0
git push origin v1.0.0
```

Triggers production deployment:
- Manual approval required
- Blue-green deployment strategy
- Health checks and validation
- Automatic rollback if issues detected

## 🧪 Testing Locally

### Run Full Test Suite
```bash
# All tests with coverage
./scripts/run_tests.sh --all --coverage --verbose

# Quick validation
./scripts/run_tests.sh --backend --frontend
```

### Individual Test Types
```bash
# Backend only (requires Docker containers)
./scripts/run_tests.sh --backend

# Frontend only
./scripts/run_tests.sh --frontend

# Integration tests
./scripts/run_tests.sh --integration

# E2E tests (requires running app)
cd frontend && npm run e2e
```

### Security Validation
```bash
# Production security check
./scripts/validate_production_security.sh

# Docker security scan
./scripts/docker_security_scan.sh
```

## 🔍 Pipeline Status & Monitoring

### Check Pipeline Status
- **GitHub Actions**: View workflow runs in the Actions tab
- **Pull Request**: Status checks show in PR interface
- **Slack Notifications**: Deployment status updates (if configured)

### Common Status Indicators
- ✅ **All checks passed**: Ready to merge
- ❌ **Tests failed**: Fix failing tests before merge
- 🟡 **In progress**: Pipeline still running
- ⚠️ **Security issues**: Address vulnerabilities

### Viewing Logs
```bash
# Using GitHub CLI
gh run list
gh run view <run-id> --log

# Or visit GitHub Actions web interface
```

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### **Test Failures**
```bash
# Run tests locally to debug
./scripts/run_tests.sh --backend --verbose
./scripts/run_tests.sh --frontend --verbose

# Check specific test files
pytest tests/test_specific.py -v
cd frontend && npm test -- --testPathPattern="ComponentName"
```

#### **Linting Issues**
```bash
# Fix formatting automatically
black .
cd frontend && npm run lint:fix

# Check manually
flake8 api/
cd frontend && npm run lint
```

#### **Build Issues**
```bash
# Test Docker build locally
docker build -t test-build .

# Check dependencies
pip install -r requirements.txt
cd frontend && npm install
```

#### **Security Scan Failures**
```bash
# Check vulnerabilities
safety check
bandit -r api/

# Update dependencies
pip install --upgrade -r requirements.txt
cd frontend && npm audit fix
```

### Getting Help
1. Check workflow logs in GitHub Actions
2. Run tests locally to reproduce issues
3. Review error messages and documentation
4. Ask team for help with complex issues

## 📊 Quality Gates

### Pre-Merge Requirements
Before your PR can be merged, it must pass:

1. ✅ **Code Formatting**: Black, ESLint compliance
2. ✅ **Linting**: Flake8, PyLint (≥8.0 score)
3. ✅ **Type Checking**: MyPy validation
4. ✅ **Security**: No high/critical vulnerabilities
5. ✅ **Tests**: All unit and integration tests pass
6. ✅ **Build**: Docker container builds successfully
7. ✅ **Coverage**: Meets coverage thresholds

### Production Requirements
For production deployment:

1. ✅ **Staging Success**: Staging deployment works
2. ✅ **E2E Tests**: All end-to-end tests pass
3. ✅ **Performance**: Load tests meet thresholds
4. ✅ **Security**: Container security scan passes
5. ✅ **Manual Approval**: Human review and approval
6. ✅ **Health Checks**: Application health validation

## 🔧 Advanced Usage

### Manual Workflow Triggers
```bash
# Trigger production deployment manually
gh workflow run production-deployment.yml \
  -f environment=production \
  -f skip_tests=false
```

### Environment-Specific Testing
```bash
# Set environment for testing
export ENVIRONMENT=staging
./scripts/run_tests.sh --integration

# Production-like testing
export ENVIRONMENT=production
./scripts/validate_production_security.sh
```

### Custom Test Configurations
```bash
# Run with specific coverage threshold
./scripts/run_tests.sh --backend --coverage
# Coverage reports in coverage/backend/

# Fast feedback loop
./scripts/run_tests.sh --fail-fast --verbose
```

## 📈 Performance Tips

### Faster Development Cycle
1. **Run Tests Locally First**: Catch issues before pushing
2. **Use Fail-Fast**: `./scripts/run_tests.sh --fail-fast`
3. **Specific Test Runs**: Target specific test files
4. **Fix Linting Early**: Use pre-commit hooks

### Optimizing CI Performance
1. **Smaller Commits**: Easier to debug failures
2. **Clear Commit Messages**: Better tracking
3. **Fix Broken Main**: Priority fix for main branch issues
4. **Cache Friendly**: Avoid unnecessary dependency changes

## 🎯 Best Practices

### Code Quality
- **Follow Conventions**: Use black, follow PEP8
- **Write Tests**: Maintain good test coverage
- **Security First**: Regular dependency updates
- **Type Hints**: Use type annotations

### Git Workflow
- **Feature Branches**: Always branch from main
- **Clear Messages**: Descriptive commit messages
- **Small PRs**: Easier to review and test
- **Rebase if Needed**: Keep history clean

### Testing Strategy
- **Test Locally**: Run tests before pushing
- **Integration Tests**: Test API endpoints
- **E2E Coverage**: Test critical user flows
- **Performance**: Monitor response times

## 📋 Checklist for Contributors

### Before Creating PR
- [ ] Run `./scripts/run_tests.sh --all` locally
- [ ] Fix any linting issues
- [ ] Ensure tests cover new functionality
- [ ] Update documentation if needed
- [ ] Check security scan results

### During PR Review
- [ ] All CI checks are green
- [ ] Code review completed
- [ ] Tests cover edge cases
- [ ] Security considerations addressed
- [ ] Performance impact assessed

### After Merge
- [ ] Monitor staging deployment
- [ ] Verify E2E tests pass
- [ ] Check for any alerts
- [ ] Plan production release if ready

## 🔗 Additional Resources

- **[Complete CI/CD Documentation](./CI_CD_PIPELINE.md)**: Comprehensive pipeline details
- **[Testing Framework](./TESTING_FRAMEWORK.md)**: Testing strategy and guidelines
- **[Security Guidelines](./security/)**: Security best practices
- **[Production Deployment](./PRODUCTION_DEPLOYMENT.md)**: Production setup guide

---

**🎉 Ready to contribute?** The CI/CD pipeline is designed to catch issues early and deploy safely. Follow this guide for a smooth development experience!