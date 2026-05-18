# Code Style Guide

All languages follow Google style guides. **When editing existing code, match the surrounding style.**

---

## Python

- **Naming:** `snake_case` for modules/functions/variables, `PascalCase` for classes, `ALL_CAPS` for constants, `_leading_underscore` for internal members
- **Line length:** 80 characters
- **Indentation:** 4 spaces, no tabs
- **Imports:** One per line, grouped: standard library → third-party → local
- **Strings:** f-strings for formatting; be consistent with quote style
- **Type annotations:** Required on all public APIs
- **Docstrings:** `"""triple double quotes"""` on every public module, function, class, and method. Format: one-line summary, then `Args:`, `Returns:`, `Raises:` sections
- **Default arguments:** Never use mutable objects (`[]`, `{}`) as defaults
- **None checks:** Use `if foo is None:`, not `if not foo:`
- **Entry point:** All executable scripts use `if __name__ == '__main__': main()`

*Source: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)*

---

## TypeScript

- **Naming:** `UpperCamelCase` for classes/interfaces/types/enums, `lowerCamelCase` for variables/functions/methods, `CONSTANT_CASE` for global constants
- **No `_` prefix/suffix** on identifiers (including private properties — use `private` modifier instead)
- **No `var`** — use `const` by default, `let` if reassignment is needed
- **No default exports** — use named exports only
- **No `any`** — use `unknown` or a specific type
- **No type assertions** (`x as T`) unless unavoidable with clear justification
- **No `#private` fields** — use TypeScript's `private` modifier
- **Semicolons:** Always. Do not rely on ASI.
- **Quotes:** Single quotes for strings; template literals for interpolation
- **Equality:** Always `===` / `!==`
- **`readonly`:** Mark properties never reassigned outside the constructor
- **`public` modifier:** Omit (it's the default)

*Source: [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)*

---

## JavaScript

- **Naming:** `UpperCamelCase` for classes, `lowerCamelCase` for functions/variables/methods, `CONSTANT_CASE` for constants
- **No `var`** — `const` by default, `let` if reassignment needed
- **No default exports** — named exports only
- **Semicolons:** Required on every statement
- **Indentation:** 2 spaces, no tabs
- **Line length:** 80 characters
- **Braces:** Required for all control structures, even single-line. K&R style.
- **Quotes:** Single quotes; template literals for multi-line or interpolation
- **Equality:** Always `===` / `!==`
- **Loops:** Prefer `for-of`. Use `for-in` only on dict-style objects.
- **Forbidden:** `eval()`, `with`, modifying built-in prototypes

*Source: [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)*

---

## HTML / CSS

- **Capitalisation:** All lowercase for element names, attributes, selectors, properties
- **Indentation:** 2 spaces, no tabs
- **Encoding:** UTF-8, specify `<meta charset="utf-8">`
- **Semantics:** Use HTML elements for their intended purpose
- **`alt` text:** Required on all images
- **CSS class naming:** `kebab-case` with meaningful names (`.video-player`, not `.vid`)
- **No ID selectors** for styling — use class selectors
- **Shorthand properties:** Use where possible (`padding`, `font`, etc.)
- **Zero values:** Omit units (`margin: 0`, not `margin: 0px`)
- **Hex notation:** Use 3-character form where possible (`#fff`)
- **`!important`:** Avoid
- **Declaration order:** Alphabetise within a rule

*Source: [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)*
