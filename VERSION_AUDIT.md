# Version consistency audit — SSL Certificate Toolkit v3.4.2

## Completed fixes

- Application and Picture Preview import `APP_VERSION` from `app_version.py` instead of maintaining competing version constants.
- Added `version_manager.py`: `--check` validates release metadata; `--set X.Y.Z` updates version-bearing app/build/release files.
- Windows numeric version (`filevers`, `prodvers`) and string metadata (`FileVersion`, `ProductVersion`, `OriginalFilename`) are included.
- `build_windows.bat` title, build banner, PyInstaller name and EXE path are included.
- GitHub Actions build name, checksum filename, artifact name, release tag and release title are included.
- README active version headings and current build output examples are included.
- Current-version tests no longer rely on fixed `3.4.2` values; tests assert dynamically against `APP_VERSION`.
- Current README installation text no longer instructs the reader to unzip v3.2.

## Remaining review items (not silently changed)

1. **Automatic GitHub Release on every main push:** `.github/workflows/build-windows.yml` builds on main, then auto-creates `vX.Y.Z` Release if absent. This may publish an unapproved/test build on any main push. Recommendation: move Release publication to a manually dispatched or tag-triggered job, while keeping CI builds for main. Needs approval because this changes release policy.
2. **Historical report:** `TEST_REPORT_v3.4.0.txt` is genuinely a historical report, not current version metadata. Keep its filename and version; consider moving it into `docs/history/` to prevent confusion.
3. **Historical README explanations:** some old v3.3.1 and v3.4.1 limitations and 'future' references remain. These describe previous releases or design aspirations and should be reviewed for present-day accuracy, not blindly version-replaced.
4. **GUI and Windows build validation:** automated tests run in this environment but Windows-specific Qt GUI smoke tests are skipped here. Run `build_windows.bat` and validate the EXE FileVersion and exported PNG version in Windows.
5. **PyInstaller output artifacts:** existing `dist/` EXEs will not be renamed or rebuilt by the version updater. Re-run the builder after changing a version.
6. **Release notes:** `--set` inserts a placeholder entry if CHANGELOG has no new section. Fill it before publishing.

## Verification

- `python version_manager.py --check`: PASSED for v3.4.2.
- `python -m unittest discover -s tests -q`: 51 tests, OK (4 skipped).
- Temporary-copy simulation: `python version_manager.py --set 3.4.3`, followed by `--check`: PASSED. Production source remains v3.4.2.
- No ZIP created; no GitHub writes performed.
