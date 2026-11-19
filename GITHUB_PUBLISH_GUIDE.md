# GitHub automatic source publishing

Repository: `cleverandy/SSL-Certificate-Toolkit-Public` — target branch: `main`.

## Important boundaries

This workflow is **a local-to-GitHub bridge**, not direct access from ChatGPT's GitHub Connector to ChatGPT's `/mnt/data` file system. The connector can create Git objects from text, but cannot dereference local paths. Run the bridge on a computer where this source directory is available. No ZIP, local `git push`, or PowerShell required.

## First-time setup (Windows)

1. Install Python 3 and [GitHub CLI](https://cli.github.com/).
2. Run `gh auth login` and authorize the account with **Contents: read/write** permissions for this repository. Never paste the resulting token into ChatGPT or a tracked source file. Alternatively set `GH_TOKEN` as an environment variable for the process.
3. In this unzipped directory, double-click `Publish_to_GitHub.bat`. It runs tests, checks current version metadata, compares remote files and previews changed paths. Only after confirmation does it upload.

Or via terminal:

```bat
python github_publisher.py
python github_publisher.py --publish --allow-auto-release
```

**Caution:** The existing `.github/workflows/build-windows.yml` executes `gh release create` on a push to `main`. Until this workflow is separately changed to tag/manual-release-only, a main push may automatically publish an EXE as a public GitHub Release. The publisher **refuses** to publish without the explicit `--allow-auto-release` flag. The `.bat` launcher also warns and asks for confirmation. Do not approve while V3.4.2 Windows testing is unfinished.

## Safety and consistency guarantees

- No branch mutation in default preview mode.
- Explicit file allowlist, including `.github/workflows/`, Python source, test files and public image assets. Private keys, certificate exports, `.env`, ZIP/EXE, caches and builds are never uploaded.
- Validates version consistency and runs `unittest` before it uploads.
- Reads current `main` HEAD and recursive Git Tree, and compares Git Blob SHA-1 checksums to determine changed/new files.
- Uploads blobs first, then creates **one** tree and **one** commit with the observed HEAD as parent. Remote-only files are preserved rather than deleted implicitly.
- Re-reads HEAD immediately before update. If someone has pushed in the meantime, it aborts without touching `main`.
- Uses non-force Git ref update, verifies HEAD and commit tree afterward.
- Outputs new commit URL and Actions URL for inspecting the Windows build. It **does not** claim CI passed or automatically wait for CI completion.

## Important details

- The remote HEAD SHA is not a configuration value to edit. It is read automatically every execution.
- GitHub API can accept writes from the local script because it has direct filesystem and authenticated HTTP access. ChatGPT's Connector cannot, on its own, read this directory.
- Local test skips due to missing PySide6 are reported as skips; Windows GUI acceptance testing still matters.
- If CI fails, investigate the Actions run. A successful source push does not imply a successful Windows EXE build.
