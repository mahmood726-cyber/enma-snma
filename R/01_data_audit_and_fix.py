#!/usr/bin/env python3
"""
NMA Methods Research: Data Audit & Fix Script (Step 1)
Purpose: Audit all datasets, identify issues, and create fix recipes
"""

import os
import csv
from collections import defaultdict
from pathlib import Path

# Set working directory -- relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
NMADATASETS_DIR = BASE_DIR / "nmadatasets" / "inst" / "extdata"
NETMETA_DIR = BASE_DIR / "netmetaDatasets" / "inst" / "extdata"

print("\n" + "="*73)
print("  NMA DATA AUDIT & FIX - Step 1")
print("="*73 + "\n")

# ============================================================================
# SECTION 1: Audit all CSV files
# ============================================================================

print("Section 1: Auditing CSV files...\n")

# Get all CSV files
all_files = []
if NMADATASETS_DIR.exists():
    all_files.extend(list(NMADATASETS_DIR.glob("*.csv")))
if NETMETA_DIR.exists():
    all_files.extend(list(NETMETA_DIR.glob("*.csv")))

print(f"Found {len(all_files)} CSV files to audit\n")

# Audit function
def audit_csv(filepath):
    result = {
        'file': filepath.name,
        'path': str(filepath),
        'status': 'OK',
        'n_rows': 0,
        'n_cols': 0,
        'columns': [],
        'issues': [],
        'sample_data': []
    }

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            if not rows:
                result['status'] = 'EMPTY'
                result['issues'].append('File is empty')
                return result

            result['n_rows'] = len(rows)
            result['n_cols'] = len(rows[0]) if rows else 0
            result['columns'] = list(rows[0].keys()) if rows else []

            # Check for issues
            # 1. Check for empty values
            for col in result['columns']:
                na_count = sum(1 for row in rows if not row.get(col) or row.get(col).strip() == '')
                if na_count > 0:
                    pct = 100 * na_count / len(rows)
                    result['issues'].append(
                        f"Column '{col}': {na_count} empty values ({pct:.1f}%)"
                    )

            # 2. Check for empty treatment names
            if 'treatment' in result['columns']:
                empty_treatments = sum(1 for row in rows
                    if not row.get('treatment') or row.get('treatment').strip() in ('', 'NA'))
                if empty_treatments > 0:
                    result['issues'].append(f"{empty_treatments} empty treatment labels")

                # Check for placeholder labels
                import re
                placeholder_count = sum(1 for row in rows
                    if row.get('treatment') and re.match(r'^\d+$|^[A-D]$', row.get('treatment', '').strip()))
                if placeholder_count > 0:
                    result['issues'].append("Contains placeholder treatment labels (numbers or A-D)")

            # 3. Check for empty study names
            if 'study' in result['columns']:
                empty_studies = sum(1 for row in rows
                    if not row.get('study') or row.get('study').strip() in ('', 'NA'))
                if empty_studies > 0:
                    result['issues'].append(f"{empty_studies} empty study labels")

                # Check for placeholder study IDs
                numeric_study_count = sum(1 for row in rows
                    if row.get('study') and re.match(r'^\d+$', row.get('study', '').strip()))
                if numeric_study_count > 0:
                    result['issues'].append("Contains numeric/placeholder study IDs")

            # 4. Check for duplicates
            if 'study' in result['columns'] and 'treatment' in result['columns']:
                seen = set()
                dup_count = 0
                for row in rows:
                    key = (row.get('study', ''), row.get('treatment', ''))
                    if key in seen:
                        dup_count += 1
                    seen.add(key)
                if dup_count > 0:
                    result['issues'].append(f"{dup_count} duplicate (study, treatment) rows")

            # Store sample data
            result['sample_data'] = rows[:3]

            # Set status
            if len(result['issues']) > 0:
                result['status'] = 'ISSUES'

    except Exception as e:
        result['status'] = 'ERROR'
        result['issues'].append(str(e))

    return result


# Run audit
audit_results = [audit_csv(f) for f in all_files]

# Summarize by status
status_summary = defaultdict(int)
for r in audit_results:
    status_summary[r['status']] += 1

print("Audit Summary:")
for status, count in sorted(status_summary.items()):
    print(f"  {status}: {count}")
print()

# Group by package
def get_package(filename):
    if 'nmadatasets' in filename:
        if 'bnma__' in filename: return 'bnma'
        if 'BUGSnet__' in filename: return 'BUGSnet'
        if 'gemtc__' in filename: return 'gemtc'
        if 'MBNMAdose__' in filename: return 'MBNMAdose'
        if 'multinma__' in filename: return 'multinma'
        if 'nmaINLA__' in filename: return 'nmaINLA'
        if 'pcnetmeta__' in filename: return 'pcnetmeta'
        if 'netmeta__' in filename: return 'netmeta'
        return 'nmadatasets_other'
    return 'netmetaDatasets'

package_summary = defaultdict(int)
for r in audit_results:
    pkg = get_package(r['path'])
    package_summary[pkg] += 1

print("Files by Package:")
for pkg, count in sorted(package_summary.items(), key=lambda x: -x[1]):
    print(f"  {pkg}: {count}")
print()

# ============================================================================
# SECTION 2: Identify Cross-Package Datasets
# ============================================================================

print("\nSection 2: Identifying Cross-Package Datasets...\n")

def get_dataset_name(filename):
    'Extract dataset name from filename'
    filename_lower = filename.lower()
    if '__smoking' in filename_lower: return 'smoking'
    if '__thrombolyt' in filename_lower: return 'thrombolytic'
    if '__parkinson' in filename_lower: return 'parkinson'
    if '__diabetes' in filename_lower: return 'diabetes'
    if '__depression' in filename_lower: return 'depression'
    if '__dietfat' in filename_lower or '__dietary' in filename_lower: return 'dietary_fat'
    if '__blocker' in filename_lower: return 'blocker'
    if '__statins' in filename_lower: return 'statins'
    # Extract from package__dataset pattern
    if '__' in filename:
        parts = filename.split('__')
        if len(parts) > 1:
            return parts[1].replace('_nodes', '').replace('_studies', '').replace('_contrast', '')
    return filename.split('_')[0]

dataset_presence = defaultdict(int)
for r in audit_results:
    ds_name = get_dataset_name(r['file'])
    dataset_presence[ds_name] += 1

print("Datasets appearing multiple times (cross-package):")
multi_presence = {k: v for k, v in sorted(dataset_presence.items(), key=lambda x: -x[1]) if v > 2}
for ds, count in multi_presence.items():
    print(f"  {ds}: {count} files")
print()

# ============================================================================
# SECTION 3: Detailed Issue Report
# ============================================================================

print("\nSection 3: Detailed Issue Report")
print("=" * 50 + "\n")

problematic = [r for r in audit_results if r['status'] in ('ISSUES', 'ERROR', 'EMPTY')]

print(f"Found {len(problematic)} files with issues\n")

for i, item in enumerate(problematic, 1):
    print(f"[{i}] {item['file']}")
    print(f"    Status: {item['status']}")
    print(f"    Size: {item['n_rows']} rows x {item['n_cols']} cols")
    print("    Issues:")
    for issue in item['issues']:
        print(f"      - {issue}")
    print()

# ============================================================================
# SECTION 4: Generate Fix Recipes
# ============================================================================

print("\nSection 4: Generating Fix Recipes")
print("=" * 40 + "\n")

fix_recipes = []

for item in problematic:
    recipe = {
        'file': item['file'],
        'path': item['path'],
        'fixes': []
    }

    for issue in item['issues']:
        if 'placeholder treatment' in issue:
            recipe['fixes'].append("Load from source package and extract treatment labels")
        elif 'numeric/placeholder study IDs' in issue:
            recipe['fixes'].append("Load from source package and extract study names")
        elif 'duplicate' in issue:
            recipe['fixes'].append("Remove duplicate (study, treatment) rows, keep first")
        elif 'empty values' in issue or 'empty treatment' in issue or 'empty study' in issue:
            recipe['fixes'].append("Impute or remove rows with empty values")
        elif 'File is empty' in issue:
            recipe['fixes'].append("Re-extract from source package")

    if recipe['fixes']:
        fix_recipes.append(recipe)

print(f"Generated {len(fix_recipes)} fix recipes\n")

# ============================================================================
# SECTION 5: Save Results
# ============================================================================

print("\nSection 5: Saving Results")
print("=" * 40 + "\n")

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Save audit summary
with open(OUTPUT_DIR / "data_audit_summary.csv", 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['file', 'status', 'n_rows', 'n_cols', 'n_issues', 'issues'])
    for r in audit_results:
        writer.writerow([
            r['file'],
            r['status'],
            r['n_rows'],
            r['n_cols'],
            len(r['issues']),
            '; '.join(r['issues'])
        ])
print("Saved: data_audit_summary.csv")

# Save problematic files detail
if problematic:
    with open(OUTPUT_DIR / "problematic_files_detail.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['file', 'status', 'issues'])
        for r in problematic:
            writer.writerow([
                r['file'],
                r['status'],
                '; '.join(r['issues'])
            ])
    print("Saved: problematic_files_detail.csv")

# Save fix recipes
if fix_recipes:
    with open(OUTPUT_DIR / "fix_recipes.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['file', 'fixes'])
        for r in fix_recipes:
            writer.writerow([
                r['file'],
                '; '.join(r['fixes'])
            ])
    print("Saved: fix_recipes.csv")

# Save cross-package dataset mapping
with open(OUTPUT_DIR / "cross_package_datasets.csv", 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['dataset', 'n_files'])
    for ds, count in sorted(dataset_presence.items(), key=lambda x: -x[1]):
        writer.writerow([ds, count])
print("Saved: cross_package_datasets.csv")

print("\n" + "="*73)
print("  AUDIT COMPLETE")
print("="*73)
print(f"\nResults saved to: {OUTPUT_DIR}")
print("\nSUMMARY:")
print(f"  Total files audited: {len(audit_results)}")
print(f"  Files with issues: {len(problematic)}")
print(f"  Cross-package datasets: {sum(1 for v in dataset_presence.values() if v > 2)}")
print("\nNext steps:")
print("  1. Review problematic_files_detail.csv")
print("  2. Apply fixes from fix_recipes.csv")
print("  3. Run cross-package comparison on clean datasets")
print()
