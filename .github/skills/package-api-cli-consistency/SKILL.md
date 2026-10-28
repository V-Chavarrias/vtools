---
name: package-api-cli-consistency
description: "Use when adding, changing, or reorganizing a package in this repository. Require every user-facing capability to work through both a reusable Python API and a CLI, with matching tests and README examples."
---

# Package API and CLI consistency

This repository contains independently installable Python packages. Every
package must provide both of these interfaces for its user-facing
functionality:

1. A reusable Python API that can be imported without parsing `sys.argv`.
2. A CLI that can be used through the installed console command and
   `python -m <package>`.

## Implementation requirements

- Put the core behavior in importable functions with explicit parameters.
- Keep CLI parsing in a thin adapter that delegates to those functions.
- Accept an optional `argv` sequence in `parse_args()` and `main()` so the CLI
  can be tested without mutating process arguments.
- Add a package `__main__.py` that calls the CLI `main()`.
- Register a console script in the package's `pyproject.toml`.
- Preserve one source of truth: the CLI and Python API must not implement
  separate versions of the same behavior.
- Keep validation and error reporting explicit at the API boundary and at the
  CLI boundary where appropriate.

## Documentation requirements

Update the package README whenever functionality changes. It must include:

- Installation from this GitHub repository.
- A direct Python import example with the required arguments.
- A console-command example.
- A `python -m <package>` example.
- Important input formats, external credentials, browser/system
  dependencies, output behavior, and resume/skip behavior.
- A clear mapping between CLI options and Python parameters when both
  interfaces expose the same capability.

## Testing requirements

- Test the core Python API independently of the CLI.
- Test that the CLI parses representative arguments and delegates to the
  Python API.
- Keep tests offline and deterministic by replacing network, browser, or
  external-service clients with fakes.
- When adding a capability, update both API and CLI tests and verify both
  README examples remain accurate.
