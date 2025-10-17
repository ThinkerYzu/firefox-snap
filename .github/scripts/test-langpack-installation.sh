#!/bin/bash
# Test that langpacks are installed in the correct directory structure
# to prevent regression of Bug 1994920
#
# Bug 1994920: Firefox 144.0-2 langpacks broke because the snap build
# script was creating directory names like "locale-fr.xpi" instead of
# "locale-fr", causing Firefox's addon system to extract the wrong ID
# from the path and reject the langpacks.

set -e

SNAP_DIR=${1:-/snap/firefox/current}
EXTENSIONS_DIR="$SNAP_DIR/usr/lib/firefox/distribution/extensions"

# Primary languages to test (subset of most common languages)
# These represent the major locales that users depend on
LANGCODES=("de" "fr" "es-ES" "ja" "zh-CN" "pt-BR" "ru" "it" "pl" "en-GB")

echo "Testing langpack installation structure..."
echo "Extensions directory: $EXTENSIONS_DIR"
echo ""

FAILED=0
CHECKED=0
MISSING=0

for LANGCODE in "${LANGCODES[@]}"; do
    LOCALE_DIR="$EXTENSIONS_DIR/locale-$LANGCODE"
    LANGPACK_FILE="$LOCALE_DIR/langpack-$LANGCODE@firefox.mozilla.org.xpi"

    # Check if locale directory exists (without .xpi in name)
    if [ ! -d "$LOCALE_DIR" ]; then
        echo "⚠️  SKIP: Directory $LOCALE_DIR not found (langpack may not be built)"
        MISSING=$((MISSING + 1))
        continue
    fi

    # Check that the wrong directory doesn't exist (Bug 1994920 regression check)
    WRONG_DIR="$EXTENSIONS_DIR/locale-$LANGCODE.xpi"
    if [ -d "$WRONG_DIR" ]; then
        echo "❌ FAIL: Wrong directory $WRONG_DIR exists (Bug 1994920 regression!)"
        echo "        Directory names must NOT contain .xpi suffix"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Check if langpack file exists
    if [ ! -f "$LANGPACK_FILE" ]; then
        echo "❌ FAIL: Langpack $LANGPACK_FILE not found in locale directory"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Verify the filename structure is correct
    # Firefox extracts the addon ID by removing .xpi from the filename
    # So "langpack-fr@firefox.mozilla.org.xpi" -> "langpack-fr@firefox.mozilla.org"
    BASENAME=$(basename "$LANGPACK_FILE" .xpi)
    EXPECTED_ID="langpack-$LANGCODE@firefox.mozilla.org"
    if [ "$BASENAME" != "$EXPECTED_ID" ]; then
        echo "❌ FAIL: Langpack has wrong name."
        echo "        Expected: $EXPECTED_ID"
        echo "        Got:      $BASENAME"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Check that there are no other files with .xpi in the addon ID
    # (e.g., langpack-fr.xpi@firefox.mozilla.org.xpi would be wrong)
    if [[ "$BASENAME" == *".xpi"* ]]; then
        echo "❌ FAIL: Addon ID contains .xpi: $BASENAME"
        echo "        This will cause Firefox to reject the langpack"
        FAILED=$((FAILED + 1))
        continue
    fi

    echo "✅ PASS: $LANGCODE langpack correctly installed"
    echo "        Directory: locale-$LANGCODE/"
    echo "        File: langpack-$LANGCODE@firefox.mozilla.org.xpi"
    CHECKED=$((CHECKED + 1))
done

echo ""
echo "========================================="
echo "Results:"
echo "  ✅ Passed:  $CHECKED"
echo "  ❌ Failed:  $FAILED"
echo "  ⚠️  Skipped: $MISSING (langpacks not built for these locales)"
echo "========================================="

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "❌ LANGPACK INSTALLATION TEST FAILED"
    echo ""
    echo "This indicates a regression of Bug 1994920 or similar issue."
    echo "Firefox requires:"
    echo "  1. Directory names: locale-LANGCODE (no .xpi suffix)"
    echo "  2. File names: langpack-LANGCODE@firefox.mozilla.org.xpi"
    echo "  3. Addon ID (from filename without .xpi): langpack-LANGCODE@firefox.mozilla.org"
    echo ""
    exit 1
fi

if [ $CHECKED -eq 0 ]; then
    echo ""
    echo "⚠️  WARNING: No langpacks found to test"
    echo "This may indicate the langpacks part did not build correctly"
    exit 1
fi

echo ""
echo "✅ ALL LANGPACK INSTALLATION TESTS PASSED"
exit 0
