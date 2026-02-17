# File Splitting Rule

## Rule

Any Python source file exceeding **500 lines** should be split into smaller sub-modules. The refactoring must **not change existing logic or behavior**.

## How to Split

1. **Create a sub-package directory** with the same name as the original module:

   ```
   # Before
   app/widgets/config_panel.py          (1100 lines)

   # After
   app/widgets/config_panel/
   ├── __init__.py                      (re-exports the main class)
   ├── config_panel.py                  (main class, imports from sub-modules)
   ├── ref_images_section.py            (reference images UI logic)
   ├── model_section.py                 (model/quality/ratio selectors)
   └── prompt_section.py                (prompt input, load file, etc.)
   ```

2. **Group by logical sections** — each sub-module should contain a cohesive set of related methods, widgets, or constants.

3. **Use `__init__.py` to re-export** the main class so existing imports remain unchanged:

   ```python
   # app/widgets/config_panel/__init__.py
   from .config_panel import ConfigPanel

   __all__ = ["ConfigPanel"]
   ```

4. **Preserve all public APIs** — external code should not need any import changes.

## Guidelines

| Aspect            | Rule                                                       |
| ----------------- | ---------------------------------------------------------- |
| **Threshold**     | Split when file exceeds 500 lines                          |
| **Target size**   | Each sub-module should be 100–300 lines                    |
| **Naming**        | Use descriptive names reflecting the section's purpose     |
| **Imports**       | Keep circular imports in check; use lazy imports if needed |
| **Tests**         | All existing tests must pass unchanged after splitting     |
| **Logic changes** | ❌ Strictly forbidden — split only, no behavior changes    |

## When to Apply

- When **creating new code** that would push a file over 500 lines
- When **modifying an existing file** that is already over 500 lines (split first, then modify)
- During **dedicated refactoring** sessions

## Priority Order for Splitting

1. Files > 1000 lines (critical)
2. Files > 700 lines (high)
3. Files > 500 lines (normal)
