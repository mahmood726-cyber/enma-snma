#!/usr/bin/env python3
"""
NMA Methods Research: Create Visualizations from Audit Results
Purpose: Visualize data audit findings

Part of the E-NMA / S-NMA project.
Author: Mahmood Ahmad
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

# Set up paths -- relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

# Load audit data
audit_df = pd.read_csv(OUTPUT_DIR / "data_audit_summary.csv")
cross_package_df = pd.read_csv(OUTPUT_DIR / "cross_package_datasets.csv")

print("\n" + "="*73)
print("  CREATING VISUALIZATIONS FROM AUDIT RESULTS")
print("="*73 + "\n")

# ============================================================================
# 1. Status Distribution (Pie Chart)
# ============================================================================

print("Creating status distribution chart...")

fig, ax = plt.subplots(figsize=(10, 8))

status_counts = audit_df['status'].value_counts()
colors = {'OK': '#2ecc71', 'ISSUES': '#f39c12', 'ERROR': '#e74c3c', 'EMPTY': '#95a5a6'}
status_colors = [colors.get(status, '#3498db') for status in status_counts.index]

wedges, texts, autotexts = ax.pie(
    status_counts.values,
    labels=status_counts.index,
    autopct='%1.1f%%',
    colors=status_colors,
    startangle=90,
    textprops={'fontsize': 12, 'weight': 'bold'}
)

# Enhance text
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(14)

ax.set_title('NMA Dataset Status Distribution\n(n=121 CSV files)', fontsize=16, weight='bold', pad=20)

plt.tight_layout()
plt.savefig(FIGURE_DIR / '01_status_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 01_status_distribution.png")

# ============================================================================
# 2. Files by Package (Bar Chart)
# ============================================================================

print("Creating files by package chart...")

# Extract package from file name
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
        return 'other'
    return 'netmetaDatasets'

audit_df['package'] = audit_df['file'].apply(get_package)

# Count by package and status
package_status = audit_df.groupby(['package', 'status']).size().unstack(fill_value=0)

# Reorder columns
status_order = ['OK', 'ISSUES', 'ERROR', 'EMPTY']
for col in status_order:
    if col not in package_status.columns:
        package_status[col] = 0
package_status = package_status[status_order]

# Sort by total files
package_status['total'] = package_status.sum(axis=1)
package_status = package_status.sort_values('total')
package_status = package_status.drop('total', axis=1)

fig, ax = plt.subplots(figsize=(12, 8))

package_status.plot(
    kind='barh',
    stacked=True,
    color=[colors[col] for col in status_order],
    ax=ax,
    edgecolor='white',
    linewidth=0.5
)

ax.set_xlabel('Number of Files', fontsize=12, weight='bold')
ax.set_ylabel('Package', fontsize=12, weight='bold')
ax.set_title('NMA Dataset Files by Package and Status\n(n=121 CSV files)', fontsize=16, weight='bold', pad=20)
ax.legend(title='Status', loc='lower right', fontsize=10)

# Add value labels
for i, (idx, row) in enumerate(package_status.iterrows()):
    cumulative = 0
    for status in status_order:
        value = row[status]
        if value > 0:
            ax.text(cumulative + value/2, i, str(int(value)),
                   ha='center', va='center', fontsize=9, color='white', weight='bold')
            cumulative += value

plt.tight_layout()
plt.savefig(FIGURE_DIR / '02_files_by_package.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 02_files_by_package.png")

# ============================================================================
# 3. Issue Types Distribution
# ============================================================================

print("Creating issue types chart...")

# Parse issues
issue_types = {
    'Empty treatment labels': 0,
    'Placeholder treatment labels': 0,
    'Empty study labels': 0,
    'Numeric/placeholder study IDs': 0,
    'Duplicate (study,treatment) rows': 0,
    'File is empty': 0
}

for issues_str in audit_df['issues']:
    if pd.isna(issues_str) or issues_str == '':
        continue
    for issue_type in issue_types.keys():
        if issue_type.lower() in issues_str.lower():
            issue_types[issue_type] += 1

# Filter zero counts
issue_types_filtered = {k: v for k, v in issue_types.items() if v > 0}

fig, ax = plt.subplots(figsize=(12, 6))

issues_df = pd.DataFrame(list(issue_types_filtered.items()), columns=['Issue Type', 'Count'])
issues_df = issues_df.sort_values('Count', ascending=False)

bars = ax.barh(issues_df['Issue Type'], issues_df['Count'],
               color='#e74c3c', edgecolor='white', linewidth=0.5)

ax.set_xlabel('Number of Files Affected', fontsize=12, weight='bold')
ax.set_ylabel('Issue Type', fontsize=12, weight='bold')
ax.set_title('Most Common Data Quality Issues in NMA Datasets\n(n=121 CSV files)', fontsize=16, weight='bold', pad=20)

# Add value labels
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2,
           f'{int(width)}', ha='left', va='center', fontsize=10, weight='bold')

ax.set_xlim(0, max(issues_df['Count']) * 1.15)

plt.tight_layout()
plt.savefig(FIGURE_DIR / '03_issue_types.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 03_issue_types.png")

# ============================================================================
# 4. Cross-Package Datasets (Horizontal Bar)
# ============================================================================

print("Creating cross-package datasets chart...")

# Filter to datasets with 3+ files
cross_package_filtered = cross_package_df[cross_package_df['n_files'] >= 3].sort_values('n_files')

fig, ax = plt.subplots(figsize=(10, 8))

bars = ax.barh(cross_package_filtered['dataset'], cross_package_filtered['n_files'],
               color='#3498db', edgecolor='white', linewidth=0.5)

ax.set_xlabel('Number of Files Across Packages', fontsize=12, weight='bold')
ax.set_ylabel('Dataset Name', fontsize=12, weight='bold')
ax.set_title('Cross-Package NMA Datasets\n(Datasets available in 3+ packages)', fontsize=16, weight='bold', pad=20)

# Add value labels
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.3, bar.get_y() + bar.get_height()/2,
           f'{int(width)}', ha='left', va='center', fontsize=10, weight='bold')

ax.set_xlim(0, max(cross_package_filtered['n_files']) * 1.15)

plt.tight_layout()
plt.savefig(FIGURE_DIR / '04_cross_package_datasets.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 04_cross_package_datasets.png")

# ============================================================================
# 5. Package Health Dashboard
# ============================================================================

print("Creating package health dashboard...")

# Calculate package health metrics
package_metrics = []
for pkg in audit_df['package'].unique():
    pkg_data = audit_df[audit_df['package'] == pkg]

    total = len(pkg_data)
    ok = len(pkg_data[pkg_data['status'] == 'OK'])
    issues = len(pkg_data[pkg_data['status'] == 'ISSUES'])
    errors = len(pkg_data[pkg_data['status'] == 'ERROR'])
    empty = len(pkg_data[pkg_data['status'] == 'EMPTY'])

    health_score = (ok / total * 100) if total > 0 else 0

    package_metrics.append({
        'package': pkg,
        'total': total,
        'ok': ok,
        'issues': issues,
        'errors': errors,
        'empty': empty,
        'health_score': health_score
    })

package_metrics_df = pd.DataFrame(package_metrics)
package_metrics_df = package_metrics_df.sort_values('health_score', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Left: Health Score Bar Chart
ax1 = axes[0]
colors_score = [plt.cm.RdYlGn(score/100) for score in package_metrics_df['health_score']]
bars = ax1.barh(package_metrics_df['package'], package_metrics_df['health_score'],
                color=colors_score, edgecolor='white', linewidth=0.5)

ax1.set_xlabel('Health Score (%)', fontsize=12, weight='bold')
ax1.set_ylabel('Package', fontsize=12, weight='bold')
ax1.set_title('Package Health Score\n(% of files without issues)', fontsize=14, weight='bold', pad=15)
ax1.set_xlim(0, 100)

# Add value labels
for bar, score in zip(bars, package_metrics_df['health_score']):
    ax1.text(score + 2, bar.get_y() + bar.get_height()/2,
            f'{score:.0f}%', ha='left', va='center', fontsize=9, weight='bold')

# Right: Status Breakdown
ax2 = axes[1]
package_metrics_df.set_index('package')[['ok', 'issues', 'errors', 'empty']].plot(
    kind='barh', stacked=True,
    color=[colors['OK'], colors['ISSUES'], colors['ERROR'], colors['EMPTY']],
    ax=ax2, edgecolor='white', linewidth=0.5
)

ax2.set_xlabel('Number of Files', fontsize=12, weight='bold')
ax2.set_ylabel('', fontsize=12)
ax2.set_title('Status Breakdown by Package', fontsize=14, weight='bold', pad=15)
ax2.legend(title='Status', loc='lower right', fontsize=9)

plt.tight_layout()
plt.savefig(FIGURE_DIR / '05_package_health_dashboard.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 05_package_health_dashboard.png")

# ============================================================================
# 6. Data Size Distribution (Rows vs Status)
# ============================================================================

print("Creating data size distribution chart...")

fig, ax = plt.subplots(figsize=(12, 6))

# Log scale for rows
audit_df['log_rows'] = np.log1p(audit_df['n_rows'])

for status in status_order:
    status_data = audit_df[audit_df['status'] == status]
    ax.hist(status_data['n_rows'], bins=30, alpha=0.6,
           label=status, color=colors[status], edgecolor='white', linewidth=0.5)

ax.set_xlabel('Number of Rows (log scale)', fontsize=12, weight='bold')
ax.set_ylabel('Frequency', fontsize=12, weight='bold')
ax.set_title('Dataset Size Distribution by Status\n(n=121 CSV files)', fontsize=16, weight='bold', pad=20)
ax.set_xscale('log')
ax.legend(title='Status', fontsize=10, loc='upper right')

plt.tight_layout()
plt.savefig(FIGURE_DIR / '06_data_size_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 06_data_size_distribution.png")

# ============================================================================
# 7. Comprehensive Summary Panel
# ============================================================================

print("Creating comprehensive summary panel...")

fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Title
fig.suptitle('NMA Dataset Audit: Comprehensive Summary',
             fontsize=20, weight='bold', y=0.98)

# 1. Status pie (top left)
ax1 = fig.add_subplot(gs[0, 0])
wedges, texts, autotexts = ax1.pie(
    status_counts.values, labels=status_counts.index,
    autopct='%1.0f', colors=status_colors, startangle=90
)
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(10)
ax1.set_title('Status Distribution', fontsize=12, weight='bold')

# 2. Package health (top middle)
ax2 = fig.add_subplot(gs[0, 1])
bars = ax2.barh(package_metrics_df['package'], package_metrics_df['health_score'],
                color=colors_score, edgecolor='white', linewidth=0.5)
ax2.set_xlim(0, 100)
ax2.set_xlabel('Health %', fontsize=10)
ax2.set_title('Package Health Score', fontsize=12, weight='bold')
ax2.tick_params(labelsize=8)

# 3. Issue types (top right - narrow)
ax3 = fig.add_subplot(gs[0, 2])
ax3.barh(issues_df['Issue Type'], issues_df['Count'], color='#e74c3c')
ax3.set_xlabel('Count', fontsize=10)
ax3.set_title('Common Issues', fontsize=12, weight='bold')
ax3.tick_params(labelsize=8)

# 4. Cross-package datasets (bottom left)
ax4 = fig.add_subplot(gs[1:, 0])
top_10_datasets = cross_package_filtered.tail(10)
bars = ax4.barh(top_10_datasets['dataset'], top_10_datasets['n_files'],
               color='#3498db', edgecolor='white', linewidth=0.5)
ax4.set_xlabel('Files', fontsize=10)
ax4.set_title('Cross-Package Datasets (Top 10)', fontsize=12, weight='bold')
ax4.tick_params(labelsize=8)

# 5. Package status breakdown (bottom middle/right)
ax5 = fig.add_subplot(gs[1:, 1:])
package_status_plot = package_status.copy()
package_status_plot = package_status_plot.loc[package_status_plot.sum(axis=1).sort_values().index]
package_status_plot.plot(kind='barh', stacked=True,
                         color=[colors[col] for col in status_order],
                         ax=ax5, edgecolor='white', linewidth=0.5)
ax5.set_xlabel('Number of Files', fontsize=10)
ax5.set_title('Files by Package and Status', fontsize=12, weight='bold')
ax5.legend(title='Status', fontsize=9, loc='lower right')
ax5.tick_params(labelsize=8)

plt.savefig(FIGURE_DIR / '07_comprehensive_summary_panel.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 07_comprehensive_summary_panel.png")

# ============================================================================
# 8. Data Quality Heatmap
# ============================================================================

print("Creating data quality heatmap...")

# Create quality matrix
packages = sorted(audit_df['package'].unique())
quality_issues = ['Empty treatment', 'Placeholder treatment', 'Empty study',
                  'Numeric IDs', 'Duplicates', 'Empty file']

quality_matrix = pd.DataFrame(0, index=packages, columns=quality_issues)

for _, row in audit_df.iterrows():
    pkg = row['package']
    issues_str = row['issues']

    if pd.isna(issues_str) or issues_str == '':
        continue

    for issue in quality_issues:
        if issue.lower() in issues_str.lower():
            quality_matrix.loc[pkg, issue] += 1

# Normalize by total files per package
for pkg in packages:
    pkg_total = len(audit_df[audit_df['package'] == pkg])
    if pkg_total > 0:
        quality_matrix.loc[pkg, :] = quality_matrix.loc[pkg, :] / pkg_total * 100

fig, ax = plt.subplots(figsize=(12, 8))

sns.heatmap(quality_matrix, annot=True, fmt='.0f', cmap='YlOrRd',
           cbar_kws={'label': '% of Files Affected'}, ax=ax,
           linewidths=0.5, linecolor='white')

ax.set_title('Data Quality Issues by Package\n(Percentage of files with each issue type)',
            fontsize=16, weight='bold', pad=20)
ax.set_xlabel('Issue Type', fontsize=12, weight='bold')
ax.set_ylabel('Package', fontsize=12, weight='bold')

plt.tight_layout()
plt.savefig(FIGURE_DIR / '08_data_quality_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 08_data_quality_heatmap.png")

# ============================================================================
# 9. Network Connectivity Analysis
# ============================================================================

print("Creating network connectivity analysis...")

# Analyze cross-package datasets for connectivity
connectivity_data = []

for _, row in cross_package_filtered.iterrows():
    dataset_name = row['dataset']
    n_files = row['n_files']

    # Estimate connectivity based on dataset name
    if 'smoking' in dataset_name.lower():
        connectivity_data.append({
            'dataset': dataset_name,
            'n_files': n_files,
            'type': 'Well-established',
            'potential': 'HIGH'
        })
    elif 'thrombolyt' in dataset_name.lower():
        connectivity_data.append({
            'dataset': dataset_name,
            'n_files': n_files,
            'type': 'Well-established',
            'potential': 'HIGH'
        })
    elif 'parkinson' in dataset_name.lower():
        connectivity_data.append({
            'dataset': dataset_name,
            'n_files': n_files,
            'type': 'Well-established',
            'potential': 'HIGH'
        })
    elif 'diabetes' in dataset_name.lower():
        connectivity_data.append({
            'dataset': dataset_name,
            'n_files': n_files,
            'type': 'Well-established',
            'potential': 'HIGH'
        })
    else:
        connectivity_data.append({
            'dataset': dataset_name,
            'n_files': n_files,
            'type': 'Other',
            'potential': 'MEDIUM'
        })

connectivity_df = pd.DataFrame(connectivity_data)

fig, ax = plt.subplots(figsize=(12, 8))

# Sort by potential and n_files
connectivity_df = connectivity_df.sort_values(['potential', 'n_files'], ascending=[True, True])
connectivity_df = connectivity_df.reset_index(drop=True)

colors_potential = {'HIGH': '#2ecc71', 'MEDIUM': '#f39c12'}

# Create horizontal bar chart colored by potential
y_positions = range(len(connectivity_df))
bars = ax.barh(y_positions, connectivity_df['n_files'],
               color=[colors_potential.get(p, '#95a5a6') for p in connectivity_df['potential']],
               edgecolor='white', linewidth=0.5)

ax.set_yticks(y_positions)
ax.set_yticklabels(connectivity_df['dataset'])

ax.set_xlabel('Number of Files Across Packages', fontsize=12, weight='bold')
ax.set_ylabel('Dataset', fontsize=12, weight='bold')
ax.set_title('Cross-Package Dataset Potential for Method Comparison\n(High potential = Primary targets for bake-off)',
            fontsize=16, weight='bold', pad=20)
ax.legend(title='Comparison Potential', fontsize=10)

plt.tight_layout()
plt.savefig(FIGURE_DIR / '09_cross_package_potential.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 09_cross_package_potential.png")

# ============================================================================
# 10. Key Statistics Summary Figure
# ============================================================================

print("Creating key statistics summary...")

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('NMA Dataset Audit: Key Statistics',
             fontsize=18, weight='bold', y=0.98)

# Flatten axes
axes_flat = axes.flatten()

# Stat 1: Total files
ax = axes_flat[0]
ax.text(0.5, 0.5, f'{len(audit_df)}', fontsize=48, weight='bold',
        ha='center', va='center', transform=ax.transAxes, color='#2c3e50')
ax.text(0.5, 0.3, 'Total Files Audited', fontsize=14,
        ha='center', va='center', transform=ax.transAxes, color='#7f8c8d')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Stat 2: Clean files
ax = axes_flat[1]
ok_count = len(audit_df[audit_df['status'] == 'OK'])
ok_pct = ok_count / len(audit_df) * 100
ax.text(0.5, 0.5, f'{ok_count}\n({ok_pct:.0f}%)', fontsize=42, weight='bold',
        ha='center', va='center', transform=ax.transAxes, color='#2ecc71')
ax.text(0.5, 0.25, 'Clean Files (OK)', fontsize=14,
        ha='center', va='center', transform=ax.transAxes, color='#7f8c8d')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Stat 3: Files with issues
ax = axes_flat[2]
issues_count = len(audit_df[audit_df['status'] == 'ISSUES'])
issues_pct = issues_count / len(audit_df) * 100
ax.text(0.5, 0.5, f'{issues_count}\n({issues_pct:.0f}%)', fontsize=42, weight='bold',
        ha='center', va='center', transform=ax.transAxes, color='#f39c12')
ax.text(0.5, 0.25, 'Files with Issues', fontsize=14,
        ha='center', va='center', transform=ax.transAxes, color='#7f8c8d')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Stat 4: Packages represented
ax = axes_flat[3]
n_packages = audit_df['package'].nunique()
ax.text(0.5, 0.5, f'{n_packages}', fontsize=48, weight='bold',
        ha='center', va='center', transform=ax.transAxes, color='#3498db')
ax.text(0.5, 0.3, 'Packages Represented', fontsize=14,
        ha='center', va='center', transform=ax.transAxes, color='#7f8c8d')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Stat 5: Cross-package datasets
ax = axes_flat[4]
n_cross_package = len(cross_package_df[cross_package_df['n_files'] >= 3])
ax.text(0.5, 0.5, f'{n_cross_package}', fontsize=48, weight='bold',
        ha='center', va='center', transform=ax.transAxes, color='#9b59b6')
ax.text(0.5, 0.3, 'Cross-Package Datasets\n(3+ packages)', fontsize=14,
        ha='center', va='center', transform=ax.transAxes, color='#7f8c8d')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Stat 6: Total issues found
ax = axes_flat[5]
total_issues = audit_df['n_issues'].sum()
ax.text(0.5, 0.5, f'{int(total_issues)}', fontsize=48, weight='bold',
        ha='center', va='center', transform=ax.transAxes, color='#e74c3c')
ax.text(0.5, 0.3, 'Total Issues Found', fontsize=14,
        ha='center', va='center', transform=ax.transAxes, color='#7f8c8d')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

plt.tight_layout()
plt.savefig(FIGURE_DIR / '10_key_statistics_summary.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: 10_key_statistics_summary.png")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*73)
print("  VISUALIZATION COMPLETE")
print("="*73)
print(f"\nCreated 10 figures saved to: {FIGURE_DIR}")
print("\nFigures created:")
print("  01_status_distribution.png - Pie chart of file statuses")
print("  02_files_by_package.png - Bar chart by package and status")
print("  03_issue_types.png - Most common issues")
print("  04_cross_package_datasets.png - Datasets across packages")
print("  05_package_health_dashboard.png - Package health metrics")
print("  06_data_size_distribution.png - Dataset sizes by status")
print("  07_comprehensive_summary_panel.png - Multi-panel overview")
print("  08_data_quality_heatmap.png - Quality issues by package")
print("  09_cross_package_potential.png - Comparison potential")
print("  10_key_statistics_summary.png - Key metrics")
print("\n" + "="*73 + "\n")
