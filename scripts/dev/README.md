# Development Scripts - Legacy Notice

**Status**: These scripts reference the old `/api/` architecture and are no longer maintained after the 2.0.0 streamlining.

## Obsolete Scripts (Reference Old Architecture)

- `auth_dev_bypass.py` - Authentication bypass for old API
- `comprehensive_integration_test.py` - Integration tests for old API
- `fix_authentication.py` - Authentication fixes for old API  
- `full_stack_function_mapper.py` - Function mapping for old API
- `init_sqlite_dev.py` - Database init for old API
- `test_all_functions.py` - Function tests for old API
- `test_features.py` - Feature tests for old API

## Current Development

For the streamlined `/app/` architecture, use:

- **Setup**: `../dev_setup.py` - Initialize development environment
- **Run App**: `cd ../../app && python main.py`
- **Run Tests**: See main testing documentation

## Migration Note

These scripts were preserved for reference but are not functional with the new streamlined architecture. They reference `from api.*` imports that no longer exist.

If you need similar functionality, it should be reimplemented for the `/app/` structure or consider using the main application's built-in features.
