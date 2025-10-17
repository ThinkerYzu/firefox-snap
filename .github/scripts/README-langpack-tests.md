# Langpack Installation Tests

## Purpose

These tests verify that Firefox language packs are installed in the correct directory structure, preventing regressions like [Bug 1994920](https://bugzilla.mozilla.org/show_bug.cgi?id=1994920).

## Background: Bug 1994920

In Firefox 144.0-2, a bug in the snap build script caused language packs to fail loading, forcing users to English. The issue was:

**Root Cause**: The build script used `basename $XPI .langpack.xpi` which didn't match actual filenames, resulting in directory names like `locale-fr.xpi` instead of `locale-fr`.

**Firefox's Behavior**:
1. Scans `/distribution/extensions/locale-LANGCODE/` directories
2. For each `.xpi` file, extracts the expected addon ID by stripping `.xpi` from filename
3. Loads `manifest.json` and compares the actual addon ID
4. **Rejects if IDs don't match**: `"File contains an add-on with an incorrect ID"`

**Example of the Bug**:
```
Wrong: /distribution/extensions/locale-fr.xpi/langpack-fr@firefox.mozilla.org.xpi
       Firefox extracts ID: "langpack-fr.xpi@firefox.mozilla.org" ❌
       Manifest contains:   "langpack-fr@firefox.mozilla.org" ❌
       Mismatch → Rejected!

Right: /distribution/extensions/locale-fr/langpack-fr@firefox.mozilla.org.xpi
       Firefox extracts ID: "langpack-fr@firefox.mozilla.org" ✅
       Manifest contains:   "langpack-fr@firefox.mozilla.org" ✅
       Match → Loaded!
```

**The Fix**: Changed to `basename $XPI .xpi` in snapcraft.yaml line 548.

## Test Scripts

### 1. `test-langpack-installation.sh` (Shell Script)

Fast, lightweight test that checks filesystem structure.

**Usage:**
```bash
# Test installed snap
./.github/scripts/test-langpack-installation.sh

# Test custom snap directory
./.github/scripts/test-langpack-installation.sh /path/to/snap/mount
```

**What it checks:**
- ✅ Directory names are `locale-LANGCODE` (no `.xpi` suffix)
- ✅ File names are `langpack-LANGCODE@firefox.mozilla.org.xpi`
- ✅ No directories with `.xpi` suffix exist (Bug 1994920 regression check)
- ✅ Addon IDs extracted from filenames are correct format

### 2. `test-langpack-installation.py` (Python Script)

Comprehensive test that also validates XPI contents.

**Usage:**
```bash
# Test installed snap
python3 ./.github/scripts/test-langpack-installation.py

# Test custom snap directory
python3 ./.github/scripts/test-langpack-installation.py /path/to/snap/mount
```

**What it checks:**
- All checks from the shell script, plus:
- ✅ XPI files are valid ZIP archives
- ✅ `manifest.json` exists and is valid JSON
- ✅ Addon ID in manifest matches expected ID from filename
- ✅ Firefox will accept the langpack (full validation)

## Tested Languages

The tests check installation for these primary languages:
- German (de)
- French (fr)
- Spanish-Spain (es-ES)
- Japanese (ja)
- Chinese-China (zh-CN)
- Portuguese-Brazil (pt-BR)
- Russian (ru)
- Italian (it)
- Polish (pl)
- English-UK (en-GB)

These represent the most commonly used Firefox locales globally.

## Integration with CI/CD

These tests can be integrated into the snap build pipeline:

### Option 1: Add to GitHub Actions workflow

```yaml
- name: Test langpack installation
  run: |
    sudo snap install ./firefox_*.snap --dangerous
    ./.github/scripts/test-langpack-installation.py
```

### Option 2: Add to snapcraft.yaml as a build check

```yaml
override-prime: |
  # ... existing langpack installation code ...

  # Run validation test
  python3 $CRAFT_PROJECT_DIR/.github/scripts/test-langpack-installation.py $CRAFT_PRIME
```

## Expected Output

### Success Example:
```
Testing langpack installation structure...
Extensions directory: /snap/firefox/current/usr/lib/firefox/distribution/extensions

✅ PASS: de langpack correctly installed
        Directory: locale-de/
        File: langpack-de@firefox.mozilla.org.xpi
        Addon ID: langpack-de@firefox.mozilla.org
✅ PASS: fr langpack correctly installed
        Directory: locale-fr/
        File: langpack-fr@firefox.mozilla.org.xpi
        Addon ID: langpack-fr@firefox.mozilla.org
...

============================================================
Results:
  ✅ Passed:  10
  ❌ Failed:  0
  ⚠️  Skipped: 0 (langpacks not built for these locales)
============================================================

✅ ALL LANGPACK INSTALLATION TESTS PASSED
```

### Failure Example (Bug 1994920 regression):
```
Testing langpack installation structure...
Extensions directory: /snap/firefox/current/usr/lib/firefox/distribution/extensions

❌ FAIL: Wrong directory locale-fr.xpi exists (Bug 1994920 regression!)
        Directory names must NOT contain .xpi suffix
❌ FAIL: Addon ID mismatch for de. Expected: langpack-de@firefox.mozilla.org, Got: langpack-de.xpi@firefox.mozilla.org
        Firefox will reject this langpack

============================================================
Results:
  ✅ Passed:  0
  ❌ Failed:  2
  ⚠️  Skipped: 8
============================================================

❌ LANGPACK INSTALLATION TEST FAILED

This indicates a regression of Bug 1994920 or similar issue.
```

## Maintenance

When adding new primary languages to the snap build, update the `PRIMARY_LANGCODES` list in both test scripts.

## References

- [Bug 1994920 - Snap 144.0-2 regressed locales from langpack](https://bugzilla.mozilla.org/show_bug.cgi?id=1994920)
- [Firefox XPIProvider.sys.mjs](https://searchfox.org/mozilla-central/source/toolkit/mozapps/extensions/internal/XPIProvider.sys.mjs#3185-3264)
- [Firefox XPIInstall.sys.mjs](https://searchfox.org/mozilla-central/source/toolkit/mozapps/extensions/internal/XPIInstall.sys.mjs#4182-4189)
