# Contributing to Whisper Transcriber

Thank you for your interest in contributing! This document provides guidelines for contributing to the Whisper Transcriber project.

## Quick Start

1. **Check [TASKS.md](TASKS.md)** for current priorities and available tasks
2. **Fork the repository** on GitHub  
3. **Clone your fork** locally
4. **Create a feature branch** for your changes
5. **Make your changes** following our guidelines
6. **Test your changes** thoroughly
7. **Update [TASKS.md](TASKS.md)** if completing tracked tasks
8. **Submit a pull request**

## Development Setup

See the [Developer Guide](docs/developer-guide/contributing.md) for detailed setup instructions.

## How to Contribute

### Reporting Issues

**⚠️ IMPORTANT: Check [TASKS.md](TASKS.md) first - it contains all known issues and current work.**

**Before creating an issue:**
- Review [TASKS.md](TASKS.md) to see if already tracked
- Search existing GitHub issues to avoid duplicates  
- Check the [troubleshooting guide](docs/user-guide/troubleshooting.md)
- Test with the latest version

**For new issues not in TASKS.md:**
- Add to [TASKS.md](TASKS.md) with appropriate priority and phase
- Create GitHub issue referencing the TASKS.md entry
- Include clear description, reproduction steps, and expected behavior
- System information (OS, Docker version, etc.)
- Relevant log messages

**Use these issue templates:**
- 🐛 **Bug Report** - Something isn't working
- ✨ **Feature Request** - Suggest new functionality  
- 📚 **Documentation** - Improve or fix documentation
- ❓ **Question** - Ask for help or clarification

### Suggesting Features

We welcome feature suggestions! Please:

1. **Check existing feature requests** first
2. **Describe the use case** and problem being solved
3. **Propose a solution** if you have ideas
4. **Consider backwards compatibility**
5. **Think about mobile users** (our primary focus)

### Code Contributions

#### What We're Looking For

**High Priority:**
- 🐛 Bug fixes with test cases
- 📱 Mobile UX improvements
- 🚀 Performance optimizations
- 📚 Documentation improvements
- ♿ Accessibility enhancements

**Medium Priority:**
- ✨ New transcription features
- 🔧 Developer experience improvements
- 🎨 UI/UX enhancements
- 🧪 Test coverage improvements

#### Development Guidelines

**Code Style:**
- **Python**: Follow PEP 8, use type hints
- **JavaScript**: Use ES6+, functional components
- **Documentation**: Clear, concise, with examples

**Commit Messages:**
Use [Conventional Commits](https://conventionalcommits.org/):
```
feat(ui): add drag-and-drop file upload
fix(api): resolve timeout on large files
docs(setup): update installation guide
test(worker): add transcription job tests
```

**Pull Request Process:**
1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure CI passes** all checks
4. **Request review** from maintainers
5. **Address feedback** promptly

## Project Principles

### Technical Principles

- **Simplicity over complexity** - Choose the straightforward solution
- **Mobile-first design** - Optimize for touch devices
- **Self-contained deployment** - Minimal external dependencies
- **Privacy-focused** - Local processing, no cloud dependencies
- **Performance matters** - Fast uploads, quick transcription

### Code Quality

- **Readability** - Code should be self-documenting
- **Testability** - Write testable, modular code
- **Maintainability** - Consider future maintenance burden
- **Security** - Validate inputs, handle errors gracefully

## Development Workflow

### Branch Naming

```
feature/add-batch-upload
fix/memory-leak-worker
docs/improve-api-reference
refactor/simplify-job-queue
```

### Testing Requirements

**For bug fixes:**
- Include test that reproduces the bug
- Verify fix resolves the issue
- Ensure no regression in existing functionality

**For new features:**
- Unit tests for core logic
- Integration tests for API endpoints
- Manual testing on mobile devices

### Documentation Requirements

**Code changes require:**
- Updated API documentation (if applicable)
- Updated user guide (if user-facing)
- Updated configuration docs (if new settings)
- Code comments for complex logic

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment:

- **Be respectful** - Treat everyone with kindness and respect
- **Be collaborative** - Help others and ask for help when needed
- **Be patient** - Remember that people have different skill levels
- **Be constructive** - Provide helpful feedback and suggestions

### Communication Channels

- **GitHub Issues** - Bug reports, feature requests
- **Pull Requests** - Code review and discussion
- **Discussions** - General questions and ideas

### Recognition

Contributors are recognized in:
- **README contributors section**
- **Release notes** for significant contributions
- **Special thanks** in major releases

## Getting Help

### For Contributors

- 📖 **Read the docs** - Start with user and developer guides
- 🔍 **Search issues** - Someone may have asked before
- 💬 **Ask questions** - Create a discussion or issue
- 🤝 **Join discussions** - Participate in existing conversations

### For Maintainers

- 📝 **Review guidelines** - Follow consistent review practices
- ⏰ **Timely responses** - Respond to contributors within 48 hours
- 🎯 **Clear feedback** - Provide actionable, specific comments
- 🎉 **Celebrate contributions** - Thank contributors for their work

## Release Process

### Version Numbers

We follow [Semantic Versioning](https://semver.org/):
- **Major (2.0.0)** - Breaking changes
- **Minor (2.1.0)** - New features, backwards compatible  
- **Patch (2.1.1)** - Bug fixes, backwards compatible

### Release Schedule

- **Patch releases** - As needed for critical fixes
- **Minor releases** - Monthly for new features
- **Major releases** - Annually or for significant changes

## Legal

### License

By contributing, you agree that your contributions will be licensed under the MIT License.

### Developer Certificate of Origin

By submitting a pull request, you certify that:

1. The contribution was created in whole or in part by you
2. You have the right to submit it under the MIT license
3. You understand and agree that the contribution is public

---

## Thank You!

Every contribution helps make Whisper Transcriber better for everyone. Whether you're fixing a typo, reporting a bug, or adding a major feature, your help is appreciated! 🙏
