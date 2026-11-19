## v3.4.2 — Responsive Accent Selector and Minimal Professional Splash (preview)

- Fixed Picture Preview / PNG export version label by sharing the application version constant.
- Corrected Windows executable numeric resource version to 3.4.2.0.
- Added 11 single-word accent choices, including Windows System accent.
- Replaced Settings accent combo with responsive rounded-square swatches and compact layout.
- Updated splash layout, theme-aware background, and author/title alignment.
- Kept native Windows title bar unchanged.

## v3.4.1 — Appearance, Watch List and Email Composer (preview)

- Compact three-button System / Light / Dark selector in the sidebar.
- Centralized ThemeManager with five persistent accent palettes and shared Qt dialog styling.
- Settings page for accent and SSL verification identity.
- Independent expandable Watch List website cards with Add / Remove adjacent.
- Editable renewal email composer; Classic Outlook integration with automatic PNG attachment when a matching fresh live SSL result is available.
- Default mailto integration (text only; attachments not supported).
- Windows background notifications, scheduled startup and Gmail API are not implemented.

## v3.4.0 — Source Preview
- SSL Watch List: persistent records, 3 concurrent checks, startup refresh, connection errors separated from last successful certificate, expiry color coding, expanded details.
- Certificate Activity Log: SQLite, bounded retention, CSV export, clearing.
- Email reminder: local .eml draft with optional previously exported PNG attachment (manual sending).
- Live certificate Subject fields shown explicitly, including missing values.
- Certificate Verification Picture heading kept on one line; version updated.
- Splash screen updated to v3.4.0.
- No automatic email delivery or external malware reputation API in this preview.

## v3.4.0 — Dark Theme & UI Refinement
- Dark mode: adjusted green, amber and red certificate status text for readability while retaining their original hue families.
- Export Picture Preview: full dark-theme styling for dialog, input fields, buttons, labels and picture controls.
- Scrollbars: replaced transparent/checkerboard tracks with solid neutral-gray tracks and lighter handles in dark mode.
- Added lightweight native PySide6 startup splash with product name, version, author and shield/check mark.
- Preserved native Windows title bar for reliable Snap, resize and system controls; custom frameless title bar deferred pending Windows testing.
- No Watch List, Activity Log, phishing API or email monitoring features in this UI maintenance release.

# v3.3.1 — UI and usability maintenance release

- Replaced tiny font-symbol navigation and disclosure icons with antialiased vector-drawn icons.
- Unified QComboBox appearance, popup list and drop-down arrows across the application.
- Replaced Appearance dropdown with a persisted System → Light → Dark cycle button; removed explanatory text.
- Moved Remove next to Add in Additional DNS Names.
- Reformatted live certificate details, expiry and Checked At timestamps in English with explicit UTC offsets.
- Added confirmed import of available live certificate Subject attributes into the CSR form.
- Added optional persisted Certificate Subject defaults with reset support.
- Added explicit Update Preview to avoid regenerating the PNG card on every keystroke.
- Added regression tests for UI structure, version consistency, and all-English labels.

## v3.3.0 — Live SSL Inspector / Appearance / Export

- Added on-demand read-only live TLS certificate inspection with fresh DNS lookups and TLS handshakes, hostname checks, trust-store handshake, expiry status and clear remarks.
- Added SAN analysis and independent comparison with current draft CSR form or last generated CSR; confirmation-only SAN import.
- Added a compact verification-picture modal with optional local checker name/email, Light/Dark themes, direct PNG save and clipboard copy. It excludes input controls and includes a real Checked At timestamp.
- Embedded SSL Checker in the primary-domain input and added Back to Generate CSR.
- Replaced binary theme toggle with remembered System / Light / Dark appearance selection, with system theme event handling.
- Added file-size checks and rejected symbolic-link output overwrites; added URL validation and non-HTTP inspection restrictions.
- Versioned executable `SSL_Certificate_Toolkit_v3.3.1.exe` with Windows file version resource; automated Windows build and attempted Release publication through GitHub Actions.
- Documented limitations: no webpage execution, but no promise of immunity from malformed TLS data; no URL phishing reputation or revocation checking.

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

### v3.4.0 Windows test hotfix
- Close SQLite activity database connections explicitly to prevent Windows WinError 32 during temporary directory cleanup.
- Update GUI smoke tests for the eight-page navigation and About sidebar position.

### v3.4.2 UI refinement (post-GUI fix)
- Match Accent Theme segmented selector styling to Appearance, with compact text, swatch spacing, and single-row responsive behavior.
- Move Settings and About navigation to the fixed bottom sidebar section.
