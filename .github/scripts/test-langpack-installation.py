#!/usr/bin/env python3

"""
Test that langpacks are installed in the correct directory structure
to prevent regression of Bug 1994920.

Bug 1994920: Firefox 144.0-2 langpacks broke because the snap build
script was creating directory names like "locale-fr.xpi" instead of
"locale-fr", causing Firefox's addon system to extract the wrong ID
from the path and reject the langpacks with "incorrect ID" error.

Firefox's langpack loading logic (XPIProvider.sys.mjs):
1. Scans /distribution/extensions/locale-LANGCODE/ directories
2. For each .xpi file, extracts expected ID from filename (strips .xpi)
3. Loads manifest.json from the XPI and gets actual addon ID
4. Compares: if expected_id != actual_id, rejects with error

This test verifies all three requirements are met:
- Directory names: locale-LANGCODE (no .xpi suffix)
- File names: langpack-LANGCODE@firefox.mozilla.org.xpi
- Addon IDs match the expected pattern
"""

import json
import os
import sys
import zipfile
from pathlib import Path


# Primary languages to test (subset of most common languages)
PRIMARY_LANGCODES = [
    'de', 'fr', 'es-ES', 'ja', 'zh-CN', 'pt-BR', 'ru', 'it', 'pl', 'en-GB'
]


def test_langpack_installation(snap_dir='/snap/firefox/current'):
    """Test that langpacks are installed in correct directory structure."""

    extensions_dir = Path(snap_dir) / 'usr/lib/firefox/distribution/extensions'

    print("Testing langpack installation structure...")
    print(f"Extensions directory: {extensions_dir}")
    print()

    if not extensions_dir.exists():
        print(f"❌ ERROR: Extensions directory does not exist: {extensions_dir}")
        return False

    passed = 0
    failed = 0
    missing = 0
    errors = []

    for langcode in PRIMARY_LANGCODES:
        locale_dir = extensions_dir / f'locale-{langcode}'
        langpack_file = locale_dir / f'langpack-{langcode}@firefox.mozilla.org.xpi'

        # Check if locale directory exists (without .xpi suffix)
        if not locale_dir.is_dir():
            print(f"⚠️  SKIP: Directory {locale_dir} not found (langpack may not be built)")
            missing += 1
            continue

        # Check that the wrong directory doesn't exist (Bug 1994920 regression)
        wrong_dir = extensions_dir / f'locale-{langcode}.xpi'
        if wrong_dir.exists():
            error = f"Wrong directory {wrong_dir} exists (Bug 1994920 regression!)"
            print(f"❌ FAIL: {error}")
            print(f"        Directory names must NOT contain .xpi suffix")
            errors.append(error)
            failed += 1
            continue

        # Check if langpack file exists
        if not langpack_file.is_file():
            error = f"Langpack {langpack_file} not found in locale directory"
            print(f"❌ FAIL: {error}")
            errors.append(error)
            failed += 1
            continue

        # Verify filename structure
        expected_id = f'langpack-{langcode}@firefox.mozilla.org'
        basename = langpack_file.stem  # filename without .xpi

        if basename != expected_id:
            error = f"Langpack has wrong name. Expected: {expected_id}, Got: {basename}"
            print(f"❌ FAIL: {error}")
            errors.append(error)
            failed += 1
            continue

        # Check that addon ID doesn't contain .xpi
        if '.xpi' in basename:
            error = f"Addon ID contains .xpi: {basename}"
            print(f"❌ FAIL: {error}")
            print(f"        This will cause Firefox to reject the langpack")
            errors.append(error)
            failed += 1
            continue

        # Verify addon ID in manifest matches filename
        try:
            with zipfile.ZipFile(langpack_file, 'r') as xpi:
                manifest_data = xpi.read('manifest.json')
                manifest = json.loads(manifest_data)

                # Extract addon ID from manifest
                addon_id = manifest.get('browser_specific_settings', {}).get('gecko', {}).get('id')
                if not addon_id:
                    # Try legacy applications field
                    addon_id = manifest.get('applications', {}).get('gecko', {}).get('id')

                if not addon_id:
                    error = f"Could not find addon ID in manifest for {langcode}"
                    print(f"❌ FAIL: {error}")
                    errors.append(error)
                    failed += 1
                    continue

                # Compare with expected ID
                if addon_id != expected_id:
                    error = f"Addon ID mismatch for {langcode}. Expected: {expected_id}, Got: {addon_id}"
                    print(f"❌ FAIL: {error}")
                    print(f"        Firefox will reject this langpack")
                    errors.append(error)
                    failed += 1
                    continue

        except zipfile.BadZipFile:
            error = f"Langpack {langpack_file} is not a valid ZIP file"
            print(f"❌ FAIL: {error}")
            errors.append(error)
            failed += 1
            continue
        except json.JSONDecodeError as e:
            error = f"Could not parse manifest.json for {langcode}: {e}"
            print(f"❌ FAIL: {error}")
            errors.append(error)
            failed += 1
            continue
        except Exception as e:
            error = f"Error reading {langpack_file}: {e}"
            print(f"❌ FAIL: {error}")
            errors.append(error)
            failed += 1
            continue

        print(f"✅ PASS: {langcode} langpack correctly installed")
        print(f"        Directory: locale-{langcode}/")
        print(f"        File: langpack-{langcode}@firefox.mozilla.org.xpi")
        print(f"        Addon ID: {addon_id}")
        passed += 1

    # Print summary
    print()
    print("=" * 60)
    print("Results:")
    print(f"  ✅ Passed:  {passed}")
    print(f"  ❌ Failed:  {failed}")
    print(f"  ⚠️  Skipped: {missing} (langpacks not built for these locales)")
    print("=" * 60)

    if failed > 0:
        print()
        print("❌ LANGPACK INSTALLATION TEST FAILED")
        print()
        print("This indicates a regression of Bug 1994920 or similar issue.")
        print("Firefox requires:")
        print("  1. Directory names: locale-LANGCODE (no .xpi suffix)")
        print("  2. File names: langpack-LANGCODE@firefox.mozilla.org.xpi")
        print("  3. Addon ID (from manifest): langpack-LANGCODE@firefox.mozilla.org")
        print()
        print("Errors encountered:")
        for error in errors:
            print(f"  - {error}")
        print()
        return False

    if passed == 0:
        print()
        print("⚠️  WARNING: No langpacks found to test")
        print("This may indicate the langpacks part did not build correctly")
        return False

    print()
    print("✅ ALL LANGPACK INSTALLATION TESTS PASSED")
    return True


if __name__ == '__main__':
    snap_dir = sys.argv[1] if len(sys.argv) > 1 else '/snap/firefox/current'

    success = test_langpack_installation(snap_dir)
    sys.exit(0 if success else 1)
