# v3.2.0 — Generic Edition

- Removed university-specific branding, default organization information, domains, application settings namespace, build output names, and documentation examples.
- Set the default example domain to `www.example.com` and additional DNS example to `portal.example.com`.
- Certificate subject defaults: country `US` (editable, mandatory), all other subject fields blank.
- Retained CSR generation, CSR/key matching, certificate inspection, PEM/PFX export, theme support, and local-only cryptography from v3.1.
- Updated tests and Windows build artifact names.

No executable is included. Windows PySide6 visual validation and EXE build are still required.

## v3.2.0 — Pre-release author / About update

- Added `Developed by cleverandy` beneath the sidebar version label.
- Added an **About** page featuring version, author, MIT license, GitHub source, program overview, feature summary, local-processing information and accurate certificate-authority / certification disclaimer.
- Added author, license and project overview to the README.
- No change to CSR, PEM, PFX or certificate-processing algorithms.

## v3.2.0 — Windows build/test fix (pre-release)

- Fixed the generic-branding test falsely flagging paths embedded by Python in generated `.venv/Scripts/activate.bat`. Scanning now excludes virtual environments, Python/Qt caches, and build output while continuing to test all first-party text source.
- Added regression checks for this exclusion and for detecting prohibited branding in actual source files.
- Configure a Windows font directory for headless Qt smoke tests when available; a font-directory warning is otherwise non-fatal.
