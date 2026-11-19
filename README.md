# SSL Certificate Toolkit v3.4.0 (Source Preview)

New in v3.4.0: SSL Watch List with up to three parallel fresh TLS inspections, persisted last-known-good certificate data and separate connection errors; startup refresh setting; local SQLite activity log for CSR/KEY and PEM/PFX outputs; exportable email reminder draft with optional previously exported verification PNG; expanded certificate Subject display; updated picture header and splash screen.

**Important:** This source preview has not been GUI-tested on Windows. No third-party phishing/malware reputation provider is integrated. The email feature creates a local .eml draft; it does not send email automatically. The tool only examines TLS endpoints and cannot certify a website is malware-free.

# SSL Certificate Toolkit v3.4.0

**Developed by** [**cleverandy**](https://github.com/cleverandy) **· MIT licensed · Generic Edition**

Windows 11 **Fluent-inspired PySide6 GUI** with a sidebar, collapsible advanced settings, and separate results pages. Core certificate/key operations remain local. Optional live inspection directly connects to the requested hostname for DNS and TLS handshakes; it never downloads or executes webpage content.

## About the project

**SSL Certificate Toolkit** is a Windows desktop application that simplifies everyday SSL/TLS certificate workflows. It combines certificate signing request (CSR) and private-key generation, CSR/certificate/key inspection, certificate-chain analysis, and PEM/PFX packaging in a single, easy-to-navigate interface. Built with Python, PySide6 and `cryptography`, the application performs cryptographic operations locally without uploading certificate files or private keys to a cloud service.

The toolkit is intended for developers, system administrators, and IT professionals who need a convenient GUI for certificate preparation and troubleshooting.

**Author:** [cleverandy](https://github.com/cleverandy)
**Version:** 3.4.0 (Generic Edition)
**License:** MIT License — see [LICENSE](LICENSE)
**Project:** https://github.com/cleverandy/SSL-Certificate-Toolkit-Public

> \*\*Certification / trust notice:\*\* This tool is not a Certificate Authority and is not certified or endorsed by a CA. The offline Certificate Viewer does not establish OS trust or revocation status; the new Live Checker attempts an actual operating-system/Python trust-store handshake but does not verify revocation or phishing reputation. The exported image is a point-in-time diagnostic, not a third-party certification. Always verify live findings with your target platform.

## Interface

Sidebar:

* **Generate CSR**: primary domain, automatic www/non-www SAN, extra SANs. Subject, Key Settings and Output Location are collapsed initially. Upon generating, a separate result page lets you view or copy the CSR, the OpenSSL Linux command, and (only after revealing) the private key.
* **Certificate Viewer**: browse CSR, private key, then CRT/PEM (all within one Load Files card). The concise summary shows CSR signature validity, certificate expiry, domain coverage, public key and key matching. Full X.509 detail is behind a collapsed section.
* **PEM / PFX Builder**: drag and drop or multi-select certificate files. Automatically classify server, intermediate and root certificates by X.509 fields and issuer signatures. Allow role overrides. Analyze before export. Export Options can be expanded to include root, choose directory, add optional matching key, and create password-protected PFX.
* **Live SSL Checker**: inspect the selected HTTPS/TLS endpoint without fetching web pages, view observed certificate issuer, SHA-256 fingerprint, expiry and trust/hostname verification; resolve A/AAAA/CNAME; compare observed SANs with the draft form or generated CSR, import SANs with confirmation, and export a clean PNG verification card or copy it to the clipboard.
* **System / Light / Dark Appearance**: sidebar dropdown defaults to the Windows app theme, listens for theme changes, and remembers manual overrides.
* **SSL Checker shortcut**: embedded in the Generate CSR primary-domain field; starts an immediate check and preserves your draft when returning.

The UX aims to be easy to scan, not to show all settings at once. It is inspired by Windows 11 Fluent patterns but is not a native WinUI 3 application.

## Default subject

|Field|Default|
|-|-|
|Country (C)|US (editable; two-letter code required)|
|State / Province (ST)|Blank|
|City / Locality (L)|Blank|
|Organization (O)|Blank|
|Organizational Unit (OU)|Blank|

All fields are editable under **Generate CSR → Certificate Subject**.

## Automatic output paths

Output is saved by default under your current Windows desktop folder (including a redirected Desktop when Windows reports one). Directory and filename use **domain label + YYYYMM**.

Example, for `www.example.com` in November 2026:

```text
Desktop\\example\_202611\\
  example\_202611.csr
  example\_202611.key
```

The builder generates additional outputs in the same naming convention (only for selected outputs):

```text
Desktop\\example\_202611\\
  example\_202611.pem
  example\_202611.pfx
  example\_202611\_verification.txt
```

Note: the prefix uses the **first domain label after removing `www.` or `\*.`**, e.g. `example`, `portal`. If the same short label is used for multiple domains in a month, change the output base directory to avoid filename collisions. Existing outputs are never overwritten without explicit approval.

## Certificate chain workflow

Import any of the following in one multi-select dialog or by dropping into the import area:

**Mode A — bundle**

```text
domain.crt
CA Bundle.txt
```

**Mode B — separate CA files**

```text
domain.crt
DigiCertCA.crt
TrustedRoot.txt
```

`CA Bundle` may contain one or more certificates. The tool reads all PEM blocks inside `.crt`, `.txt`, `.pem`, or an individual DER certificate, deduplicates identical certificates, and builds a chain based on issuer signature verification. It will show incomplete-chain/expiry warnings rather than claiming platform trust.

PEM output is **server certificate + intermediate(s) + optional root** (no private key). This is compatible with the user's usual concatenation workflow. For **PFX**, select the corresponding `.key`, enter a password (minimum 8 characters) and use AES-256/SHA-256 by default. Legacy 3DES/SHA-1 is opt-in and weaker.

All output is parsed/validated again before being saved. Chain validation does **not** include OS/browser trust-anchor checks, revocation, or target-specific F5/IIS import tests.

## Build on Windows

Recommended: **Python 3.12 x64 Windows Installer**, with Python Launcher `py` installed. No special PATH variables are required if `py -3.12 --version` works. You can build from source on Windows. Prebuilt EXE availability depends on a successful GitHub Actions build and Release.

1. Extract the ZIP file on Windows.
2. Double-click `build\_windows.bat` (first run needs internet access to install packages).
3. After tests and compilation, find the app at:

```text
dist\\SSL\_Certificate\_Toolkit\_v3.3.1.exe
```

PyInstaller packs the Python interpreter, PySide6/Qt and `cryptography` into a standalone Windows executable, but the compiled program must be tested on the actual Windows target OS. The automated branding test checks first-party source files only; generated `.venv`, `build`, and `dist` folders are intentionally excluded. A Qt offscreen font-directory warning during GUI smoke tests is not by itself a build failure. The receiving PC does not need Python or OpenSSL.

For Python source debugging after dependencies are installed:

```cmd
run\_debug\_windows.bat
```

For launch without an attached CMD window, use `run\_windows.bat`.

Or manually:

```cmd
py -3.12 -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
python app.py
```

## Security / caveats

* No network upload. Keys are generated/processed locally.
* Private key output is **unencrypted PKCS#8** for web server deployment and must have appropriate NTFS ACL permissions.
* The key is hidden until explicitly revealed. Copying a private key to the clipboard has privacy implications.
* `.pfx` files are protected by the chosen password, but keep the file and password separate.
* The default certificate builder includes the Trusted Root when imported. Some TLS platforms prefer sending **only the leaf + intermediate CA**; uncheck *Include Trusted Root* where appropriate.
* Qt/PySide6 is a new frontend on top of the tested `core.py`. The cryptographic core has automated tests, but GUI runtime testing on a Windows PC remains necessary.

## Internal structure

```text
app.py                  PySide6 GUI
core.py                 Certificate generation, analysis, export and validation
requirements.txt        Python dependencies
build\_windows.bat       Windows EXE build
run\_windows.bat         Run GUI detached via pythonw.exe
run\_debug\_windows.bat   Run GUI with an attached console for debugging
assets/check\_white.png  Checked checkbox tick icon for light/dark themes
tests/test\_core.py      Unit tests
.github/workflows/      Optional Windows GitHub Actions build
```

\---

## v3.2 — GUI and usability fixes (November 2026)

v3.2 preserves the v3 certificate processing features, with the following changes:

* **Startup + blank PEM/PFX tab fixed:** The old release declared two different methods named `\_build\_bundle`. Python replaced the initial UI constructor with the export method, which inadvertently attempted chain analysis at launch. The page initializer is now `\_build\_bundle\_page`; export remains `\_build\_bundle`.
* **No premature chain errors:** The Analyze Chain and Build PEM/PFX buttons remain disabled until certificates have actually been imported. The import panel is visible at startup.
* **Dark mode checkbox readability:** High-contrast checkbox indicators, an explicit outline, and white tick mark are used in both Light and Dark mode. Assets are included in the standalone EXE packaging.
* **Dark mode pop-up readability:** Warning/error/confirmation dialogs use an explicit palette for the background, text, and buttons matching the current theme, rather than relying on the Windows dialog palette.
* **Certificate Viewer:** Inputs are in one Load Files card, ordered **CSR → Private Key → CRT/PEM**, emphasizing CSR/KEY matching. The optional encrypted-key passphrase is tucked into a collapsible sub-section. The result summary starts with CSR/KEY matching when available.
* **One-click post-generation verification:** The results view has a **Verify CSR / Key in Certificate Viewer** button. Files saved during the current session are passed through automatically to prevent incorrectly constructed file paths; inspection also works directly from freshly generated data without saving.
* **File dialog folder memory:** All certificate/key/CSR import dialogs and the multiple-file certificate import share the most recently selected directory; it persists between sessions using Qt `QSettings`. It stores **only a folder path**, not keys or passwords.
* **Safer missing-path diagnostics:** When a selected CSR/key/CRT file is not found, the message identifies the missing file and recommends Browse.
* **Detached Windows launch:** Double-click `run\_windows.bat` to launch via `pythonw.exe`, which is not tied to the lifetime of CMD. For diagnosing Python tracebacks, use `run\_debug\_windows.bat`.
* **Unexpected error diagnostics:** The app keeps a local `error.log` at `%LOCALAPPDATA%\\SSL\_Certificate\_Toolkit\\logs\\error.log`. No key/CSR/PEM buffers are intentionally logged, but error traces may include local file paths.

### Updated launch and build instructions

1. Unzip v3.2 into a **new directory** (do not mix it with v3.0 source files).
2. Double-click `build\_windows.bat` to install dependencies, run automated tests, and compile the standalone EXE. It also bundles `assets\\check\_white.png` for the checkbox icon.
3. To launch the GUI directly without a console, double-click `run\_windows.bat`.
4. To debug in CMD, double-click `run\_debug\_windows.bat`.
5. For an independent GUI program with no Python installation or CMD window, run `dist\\SSL\_Certificate\_Toolkit\_v3.3.1.exe`.

**Validation limits:** The source package is generated and tested in a Linux tool environment. The cryptographic core and source-level GUI regression tests pass; live Qt/Windows GUI tests require running the included test suite on a Windows host with PySide6 installed. The package does **not** contain a precompiled Windows executable.

## Privacy and affiliation

This is a general-purpose, local-only certificate utility. It is not affiliated with or endorsed by any university or certificate authority. Private keys and certificate material are processed locally. Review generated files and validate chains independently before production use.

## Application credits and licensing

Copyright © 2026 cleverandy. Licensed under the MIT License. See the `LICENSE` file for terms. The application includes third-party Python libraries governed by their own licenses.

## Live SSL Checker: scope and safety

* Live checks use DNS and TLS only, with fresh sockets and TLS contexts on every check. No HTTP requests, webpages, cookies, JavaScript, scripts or downloads are executed. The endpoint receives a TLS connection; the URL path is ignored.
* Invalid schemes, embedded URL credentials, query strings and control characters are rejected. The network checker uses timeouts and size limits, but connecting to a malicious TLS server still exposes the local TLS/certificate parsers to untrusted data; this is **not a malware scanner**.
* CA trust is determined with a second verified TLS handshake against the host, and results can differ across CDN/Load Balancer nodes. Revocation (OCSP/CRL) and malicious site/phishing reputation are NOT checked in v3.3.1.
* Light-theme PNG exports are the default, dark theme optional. Checker name (60 characters max) and contact email (120 characters max) are optional and stored locally in `QSettings`; these fields are plain-text report annotations, not identity verification. No keys or certificate/private-key contents are included in the image.
* Imported files are locally capped at 5 MiB (private keys 1 MiB). These are baseline safeguards, not a complete security audit.
* Future v3.3.1: deeper hardening, dependency vulnerability audit, NTFS ACL/atomic-write review and Windows adversarial/GUI tests. Future v3.4: optional external threat-intelligence checks with clear privacy and service-license disclosures.



### v3.4.0 UI maintenance

Improved dark theme colors, dialog controls and scrollbar tracks; added lightweight Qt splash screen. Windows native title bar is retained.
