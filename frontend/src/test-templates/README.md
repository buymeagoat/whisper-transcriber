# Frontend Test Templates

This directory contains standardized templates for different types of frontend tests. These templates provide consistent patterns and comprehensive coverage for React components, services, hooks, and pages.

## Available Templates

### ComponentTestTemplate.test.jsx
**Purpose**: Testing individual React components
**Use For**: UI components, form components, display components

**Key Features**:
- Rendering tests with different props
- User interaction testing (clicks, inputs, keyboard navigation)
- State management verification
- API integration testing
- Error handling and accessibility
- Performance testing for large datasets

**Usage**:
1. Copy the template to your component's `__tests__` directory
2. Replace `MockComponent` with your actual component
3. Uncomment and configure service mocks as needed
4. Customize test cases based on component functionality

### PageTestTemplate.test.jsx
**Purpose**: Testing page-level components
**Use For**: Route components, layout pages, dashboard pages

**Key Features**:
- Page rendering with routing context
- Data loading and error states
- URL parameter handling
- Navigation testing
- Form submissions and search functionality
- Responsive behavior testing
- SEO and metadata validation

**Usage**:
1. Copy template to your page's `__tests__` directory
2. Replace mock components with actual page components
3. Configure route parameters and navigation mocks
4. Add page-specific data loading and interaction tests

### ServiceTestTemplate.test.js
**Purpose**: Testing service layer modules
**Use For**: API clients, data transformation services, utility services

**Key Features**:
- CRUD operations testing
- Authentication and authorization
- Error handling (network, validation, server errors)
- Request retry and caching logic
- Data transformation validation
- Performance testing with large datasets

**Usage**:
1. Copy template to your service's `__tests__` directory
2. Replace mock service with your actual service
3. Configure axios mocks for your API endpoints
4. Add service-specific business logic tests

### HookTestTemplate.test.js
**Purpose**: Testing custom React hooks
**Use For**: State management hooks, effect hooks, context hooks

**Key Features**:
- Hook initialization and default values
- State updates and side effects
- Cleanup and memory management
- Context integration testing
- Performance optimization validation
- Edge case handling

**Usage**:
1. Copy template to your hook's `__tests__` directory
2. Replace `useMockHook` with your actual hook
3. Add hook-specific logic and state management tests
4. Test integration with external dependencies

## Template Customization Guidelines

### 1. Component Naming
- Replace all template placeholders with actual names
- Use consistent naming conventions
- Update import statements and file paths

### 2. Mock Configuration
- Uncomment relevant service mocks
- Configure mock responses based on your API
- Set up context providers for components that need them

### 3. Test Data Setup
- Create realistic mock data that matches your API responses
- Use factories or builders for complex mock objects
- Ensure test data covers edge cases and error scenarios

### 4. Assertion Customization
- Replace generic assertions with specific ones for your component
- Test actual functionality rather than implementation details
- Focus on user-facing behavior and outcomes

### 5. Accessibility Testing
- Customize ARIA label and role assertions
- Test keyboard navigation specific to your component
- Add screen reader compatibility tests

## Common Patterns

### API Integration Testing
```javascript
// Setup mock
serviceName.fetchData.mockResolvedValue(mockData);

// Test component behavior
renderComponent();
await waitFor(() => {
  expect(screen.getByText('Expected Content')).toBeInTheDocument();
});

// Verify API call
expect(serviceName.fetchData).toHaveBeenCalledWith(expectedParams);
```

### User Interaction Testing
```javascript
const user = userEvent.setup();

// Simulate user actions
await user.click(screen.getByRole('button', { name: /submit/i }));
await user.type(screen.getByRole('textbox'), 'test input');

// Verify outcomes
expect(mockCallback).toHaveBeenCalledWith('test input');
```

### Error State Testing
```javascript
// Mock error response
serviceName.fetchData.mockRejectedValue(new Error('API Error'));

renderComponent();

// Verify error handling
await waitFor(() => {
  expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
});
```

### Loading State Testing
```javascript
// Mock pending promise
serviceName.fetchData.mockImplementation(() => new Promise(() => {}));

renderComponent();

// Verify loading indicators
expect(screen.getByRole('progressbar')).toBeInTheDocument();
expect(screen.getByText(/loading/i)).toBeInTheDocument();
```

## Best Practices

### 1. Test Organization
- Group related tests using `describe` blocks
- Use descriptive test names that explain the expected behavior
- Start with basic rendering tests, then move to interactions

### 2. Mock Management
- Reset mocks in `beforeEach` to ensure test isolation
- Mock external dependencies but not the code under test
- Use realistic mock data that reflects actual usage

### 3. Async Testing
- Always use `waitFor` for async operations
- Test both success and error cases for async operations
- Verify loading states during async operations

### 4. Accessibility
- Test keyboard navigation and focus management
- Verify ARIA attributes and semantic HTML
- Test screen reader compatibility with appropriate roles

### 5. Performance
- Test components with large datasets
- Measure render times for performance-critical components
- Verify proper cleanup and memory management

## Integration with Test Infrastructure

### Coverage Requirements
- Follow the coverage thresholds defined in `jest.config.js`
- Aim for comprehensive test coverage while focusing on quality
- Use coverage reports to identify untested code paths

### CI/CD Integration
- All tests must pass before code can be merged
- Coverage reports are generated automatically
- Performance tests help identify regressions

### Test Utilities
- Use global test utilities from `setupTests.js`
- Leverage common mock factories and helpers
- Extend utilities as needed for specific use cases

## Troubleshooting Common Issues

### 1. Component Not Rendering
- Check that all required props are provided
- Verify mock services are configured correctly
- Ensure test wrapper includes necessary providers

### 2. Async Test Failures
- Use proper `await` and `waitFor` patterns
- Check that promises resolve/reject as expected
- Verify cleanup is happening in `afterEach`

### 3. Mock Not Working
- Ensure mocks are configured before component renders
- Check mock import paths and module resolution
- Verify mocks are reset between tests

### 4. Performance Test Issues
- Adjust performance thresholds based on CI environment
- Use consistent test data sizes
- Account for slower CI environments in thresholds

## Contributing to Templates

### Adding New Templates
1. Create template following existing patterns
2. Include comprehensive test scenarios
3. Add documentation and usage examples
4. Update this README with template information

### Improving Existing Templates
1. Add missing test scenarios
2. Improve mock configurations
3. Enhance accessibility testing
4. Update documentation and examples

### Template Standards
- Use TypeScript-compatible patterns
- Include error boundaries and edge cases
- Follow established naming conventions
- Provide clear customization guidance