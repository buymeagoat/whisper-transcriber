# Frontend Development Environment

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Linting and formatting
npm run lint
npm run lint:fix
npm run format
npm run format:check
```

## Development Server

The development server runs on `http://localhost:3002` with:
- ✅ Hot Module Replacement (HMR)
- ✅ Fast refresh for React components
- ✅ API proxy to backend (`/api` → `http://localhost:8000`)
- ✅ Source maps for debugging
- ✅ Error overlay

## Environment Variables

Configuration is managed through environment variables with Vite's `import.meta.env`:

### Development (`.env.development`)
- `VITE_API_URL`: Backend API URL (default: `http://localhost:8000`)
- `VITE_DEBUG`: Enable debug mode (default: `true`)
- `VITE_ENABLE_DEBUG_TOOLS`: Show dev tools panel (default: `true`)

### Production (`.env.production`)
- `VITE_API_URL`: Backend API URL (default: `/api`)
- `VITE_DEBUG`: Enable debug mode (default: `false`)
- `VITE_ENABLE_DEBUG_TOOLS`: Show dev tools panel (default: `false`)

### Local Override
Create `.env.local` to override any environment variables locally (gitignored).

## Code Quality

### ESLint
- Configured for React 18+ with hooks
- Custom rules for consistent code style
- Run with `npm run lint` or `npm run lint:fix`

### Prettier
- Consistent code formatting
- Run with `npm run format`
- Check formatting with `npm run format:check`

### Import Aliases
- `@/` → `./src/`
- `@components/` → `./src/components/`
- `@pages/` → `./src/pages/`
- `@services/` → `./src/services/`
- `@config/` → `./src/config/`
- `@context/` → `./src/context/`

## Development Tools

### Error Boundary
- Catches React errors in development and production
- Shows user-friendly error messages
- Displays error details in development mode

### Dev Tools Panel
- Available in development mode (purple bug icon, bottom-right)
- Shows environment info, feature flags, and debug utilities
- Quick actions: clear storage, clear console, log debug info

### API Debugging
- Automatic request/response logging in development
- Configurable through `VITE_DEBUG` environment variable

## Build Optimization

### Production Build
- Code splitting with manual chunks for optimal loading
- Tree shaking to eliminate dead code
- CSS and JS minification
- Source maps generation (configurable)

### Bundle Analysis
```bash
npm run analyze
```

## Proxy Configuration

API calls to `/api/*` are automatically proxied to the backend server:
- Development: `http://localhost:8000`
- Production: Served by the same domain

## Troubleshooting

### Dev Server Issues
```bash
# Clear Vite cache and restart
npm run dev:clean
```

### Build Issues
```bash
# Type checking
npm run type-check

# Clean install
rm -rf node_modules package-lock.json
npm install
```

### Hot Reload Not Working
- Check file extensions (.jsx for components)
- Ensure components are exported correctly
- Restart dev server if issues persist

## Architecture

```
src/
├── components/     # Reusable UI components
├── pages/         # Route components
├── context/       # React context providers
├── services/      # API services and utilities
├── config/        # Environment configuration
└── assets/        # Static assets
```

## Best Practices

1. **Components**: Use functional components with hooks
2. **State**: Use React Context for global state, local state for component-specific data
3. **API**: All API calls through service modules in `/services/`
4. **Styling**: Tailwind CSS with dark mode support
5. **Error Handling**: Use ErrorBoundary for component errors, try/catch for async operations
6. **Performance**: Use React.memo, useMemo, useCallback where appropriate
