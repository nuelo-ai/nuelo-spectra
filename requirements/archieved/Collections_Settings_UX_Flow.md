# Collections & Settings - Detailed User Experience Flow

## Document Overview

This document provides a comprehensive user experience specification for the "Collections" and "Settings" modules. Collections serves as the central repository for user-uploaded files and saved outputs from the Chat with Data feature, while Settings provides account management, subscription control, and security functions. This guide is intended for UI/UX designers to create detailed interface designs ensuring consistent implementation across the product.

The following sections detail:

- **Collections Module** — File management for uploaded files (view, download, delete), saved reports from Chat with Data queries, and generated PowerPoint presentations
- **Settings Module** — Account profile management, subscription and credit controls, password security, and session management
- **Error Handling & Edge Cases** — System responses for file operations, payment failures, and validation scenarios
- **Supporting Elements** — Loading states, confirmation dialogs, accessibility requirements, and mobile responsiveness

> **Note:** File uploads are managed separately from the Dashboard. The Collections module only provides viewing and management of already uploaded files.

---

# Module: Collections

## 1. Entry Point: Collections Screen

### 1.1 Accessing Collections

**Navigation:** User clicks "Collections" in the main navigation sidebar

**System Response:**
- Page transitions with smooth animation
- Collections dashboard loads with default view (Uploaded Files tab)
- Loading skeleton appears briefly while content fetches

### 1.2 Collections Dashboard Layout

**Screen:** Collections Main View

```
┌─────────────────────────────────────────────────────────────────┐
│  Header Bar                                                      │
│  [≡ Menu]  Collections                    [🔍 Search] [👤 User] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  [Uploaded Files]  [Saved Reports]  [PowerPoints]       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📁 Uploaded Files                                       │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │                                                          │    │
│  │  Sort by: [Name ▼]  Filter: [All Types ▼]  View: [≡][⊞] │    │
│  │                                                          │    │
│  │  ┌────┬──────────────┬────────┬──────────┬───────────┐  │    │
│  │  │ ☐  │ Name         │ Type   │ Size     │ Uploaded  │  │    │
│  │  ├────┼──────────────┼────────┼──────────┼───────────┤  │    │
│  │  │ ☐  │ sales_q4.csv │ CSV    │ 2.4 MB   │ Jan 15    │  │    │
│  │  │ ☐  │ report.xlsx  │ Excel  │ 1.1 MB   │ Jan 14    │  │    │
│  │  │ ☐  │ data.json    │ JSON   │ 540 KB   │ Jan 12    │  │    │
│  │  └────┴──────────────┴────────┴──────────┴───────────┘  │    │
│  │                                                          │    │
│  │  Showing 3 of 3 files                    [◀ 1 of 1 ▶]   │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Tab Navigation

| Tab | Description | Icon |
|-----|-------------|------|
| Uploaded Files | User-uploaded data files for analysis | 📁 |
| Saved Reports | Data Cards saved from Chat with Data | 📊 |
| PowerPoints | Generated presentation files | 📽️ |

**Tab Behavior:**
- Active tab highlighted with underline and bold text
- Tab count badge shows number of items (e.g., "Uploaded Files (12)")
- Click tab to switch view with fade transition
- URL updates to reflect active tab for bookmarking

---

## 2. Uploaded Files Management

### 2.1 File List View

**Default State:** List view showing all uploaded files

**Table Columns:**

| Column | Description | Sortable | Default Sort |
|--------|-------------|----------|--------------|
| Checkbox | Multi-select for bulk actions | No | — |
| Name | File name with icon | Yes | — |
| Type | File format (CSV, Excel, JSON, etc.) | Yes | — |
| Size | File size in KB/MB | Yes | — |
| Uploaded | Upload date | Yes | Descending (newest first) |
| Actions | Quick action buttons | No | — |

**Row Interactions:**
- Hover: Row highlights, action buttons appear
- Click row: Opens file preview/details panel
- Right-click: Context menu with all actions

### 2.2 Download File

**Method 1: Quick Action**

**User Action:** Click download icon (⬇️) on file row

**System Response:**
1. Download starts immediately
2. Browser's native download manager handles file
3. Toast notification: "Downloading sales_q4.csv..."

**Method 2: Context Menu**

**User Action:** Right-click file row → Select "Download"

**System Response:** Same as Method 1

**Method 3: Bulk Download**

**User Action:** 
1. Select multiple files via checkboxes
2. Click "Download Selected" button in bulk action bar

**System Response:**
```
┌─────────────────────────────────────────────────────────────┐
│  ☑ 3 files selected          [⬇️ Download] [🗑️ Delete]     │
└─────────────────────────────────────────────────────────────┘
```
- Files download as ZIP archive
- Toast: "Downloading 3 files as archive..."

### 2.3 Delete File

**Method 1: Single File Delete**

**User Action:** Click delete icon (🗑️) on file row

**System Response:**

**Confirmation Dialog:**
```
┌─────────────────────────────────────────────────────────────┐
│  Delete File                                          [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ Are you sure you want to delete this file?             │
│                                                             │
│     📄 sales_q4.csv (2.4 MB)                               │
│                                                             │
│  This action cannot be undone. Any analysis linked to      │
│  this file will no longer have access to the data.         │
│                                                             │
│                           [Cancel]  [🗑️ Delete]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User Action:** Click "Delete"

**System Response:**
- Dialog closes
- File row animates out (fade + collapse)
- Toast: "File deleted successfully"

**Method 2: Bulk Delete**

**User Action:**
1. Select multiple files via checkboxes
2. Click "Delete" in bulk action bar

**System Response:**

**Confirmation Dialog:**
```
┌─────────────────────────────────────────────────────────────┐
│  Delete Files                                         [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ Are you sure you want to delete 3 files?               │
│                                                             │
│     📄 sales_q4.csv                                        │
│     📄 report.xlsx                                         │
│     📄 data.json                                           │
│                                                             │
│  This action cannot be undone.                             │
│                                                             │
│                           [Cancel]  [🗑️ Delete All]        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Empty State - Uploaded Files

**Display when no files exist:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                      ┌───────────┐                          │
│                      │    📁     │                          │
│                      │   ────    │                          │
│                      └───────────┘                          │
│                                                             │
│              No files uploaded yet                          │
│                                                             │
│     Upload your data files from the Dashboard to           │
│        start analyzing them with Chat with Data.            │
│                                                             │
│                    [Go to Dashboard]                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Saved Reports Management

### 3.1 Saved Reports View

**Context:** Reports saved from Data Cards in Chat with Data

**User Action:** Click "Saved Reports" tab

**Screen Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  [Uploaded Files]  [Saved Reports]  [PowerPoints]               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 Saved Reports                           [Sort: Newest ▼]    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📊 Top 10 Products by Revenue - Q4 2024                 │    │
│  │    Source: sales_q4.csv  •  Saved: Jan 15, 2025         │    │
│  │    [View] [Export] [Delete]                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📊 Monthly Revenue Trend Analysis                        │    │
│  │    Source: revenue_2024.xlsx  •  Saved: Jan 14, 2025    │    │
│  │    [View] [Export] [Delete]                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📊 Category Comparison Report                            │    │
│  │    Source: sales_q4.csv  •  Saved: Jan 12, 2025         │    │
│  │    [View] [Export] [Delete]                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Report Card Information

Each saved report displays:

| Element | Description |
|---------|-------------|
| Icon | 📊 Report indicator |
| Title | User-defined name or Query Brief from Data Card |
| Source | Original data file used for the query |
| Saved Date | When the report was saved |
| Action Buttons | View, Export, Delete |

### 3.3 View Saved Report

**User Action:** Click "View" button on report card

**System Response:**

**Report Detail Modal:**
```
┌─────────────────────────────────────────────────────────────┐
│  Top 10 Products by Revenue - Q4 2024               [✕]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  QUERY BRIEF                                                │
│  ─────────────────────────────────────────────────────────  │
│  Top 10 products by revenue for each category in Q4 2024   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DATA TABLE                                                 │
│  ─────────────────────────────────────────────────────────  │
│  ┌──────────┬────────────┬───────────┬──────────┐          │
│  │ Rank     │ Product    │ Category  │ Revenue  │          │
│  ├──────────┼────────────┼───────────┼──────────┤          │
│  │ 1        │ Product A  │ Electronics│ $45,230 │          │
│  │ 2        │ Product B  │ Electronics│ $38,100 │          │
│  │ ...      │ ...        │ ...       │ ...      │          │
│  └──────────┴────────────┴───────────┴──────────┘          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EXPLANATION                                                │
│  ─────────────────────────────────────────────────────────  │
│  Electronics dominates with 6 out of 10 spots...           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  VISUALIZATION                                              │
│  ─────────────────────────────────────────────────────────  │
│  [Bar Chart Display]                                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Meta Information                                           │
│  Source: sales_q4.csv  |  Created: Jan 15, 2025, 2:30 PM   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [📊 Export to PPT] [📤 Share] [🔄 Re-run Query] [Close]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Export Saved Report

**User Action:** Click "Export" button

**Export Options Dropdown:**
```
┌─────────────────────┐
│ Export as...        │
├─────────────────────┤
│ 📊 PowerPoint       │
│ 📄 PDF              │
│ 🖼️ Image (PNG)      │
│ 📋 CSV (data only)  │
└─────────────────────┘
```

**Export Process:**
1. User selects format
2. Brief processing indicator
3. File downloads automatically
4. Toast: "Report exported as [format]"

### 3.5 Delete Saved Report

**User Action:** Click "Delete" button

**Confirmation Dialog:**
```
┌─────────────────────────────────────────────────────────────┐
│  Delete Report                                        [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ Are you sure you want to delete this report?           │
│                                                             │
│     📊 Top 10 Products by Revenue - Q4 2024                │
│                                                             │
│  This action cannot be undone.                             │
│                                                             │
│                           [Cancel]  [🗑️ Delete]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.6 Empty State - Saved Reports

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                      ┌───────────┐                          │
│                      │    📊     │                          │
│                      │   ────    │                          │
│                      └───────────┘                          │
│                                                             │
│              No saved reports yet                           │
│                                                             │
│     Save Data Cards from Chat with Data to access          │
│              them here anytime.                             │
│                                                             │
│                 [Go to Chat with Data]                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Generated PowerPoints Management

### 4.1 PowerPoints View

**Context:** PowerPoint files generated from Data Cards

**User Action:** Click "PowerPoints" tab

**Screen Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  [Uploaded Files]  [Saved Reports]  [PowerPoints]               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📽️ Generated PowerPoints                  [Sort: Newest ▼]     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📽️ Q4_Revenue_Analysis.pptx                     1.2 MB │    │
│  │    Generated: Jan 15, 2025  •  3 slides                 │    │
│  │    [Preview] [Download] [Delete]                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📽️ Product_Performance_Report.pptx              890 KB │    │
│  │    Generated: Jan 14, 2025  •  1 slide                  │    │
│  │    [Preview] [Download] [Delete]                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 PowerPoint Card Information

| Element | Description |
|---------|-------------|
| Icon | 📽️ PowerPoint indicator |
| File Name | Auto-generated or user-defined name |
| File Size | Size in KB/MB |
| Generated Date | Creation timestamp |
| Slide Count | Number of slides in presentation |
| Action Buttons | Preview, Download, Delete |

### 4.3 Preview PowerPoint

**User Action:** Click "Preview" button

**System Response:**

**Preview Modal:**
```
┌─────────────────────────────────────────────────────────────┐
│  Q4_Revenue_Analysis.pptx                             [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │             [Slide Preview Image]                    │   │
│  │                                                      │   │
│  │    ┌─────────────────────────────────────────┐      │   │
│  │    │  Q4 Revenue Analysis                     │      │   │
│  │    │                                          │      │   │
│  │    │  Top 10 Products by Revenue             │      │   │
│  │    │  [Chart Preview]                         │      │   │
│  │    │                                          │      │   │
│  │    └─────────────────────────────────────────┘      │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│            [◀ Previous]  Slide 1 of 3  [Next ▶]            │
│                                                             │
│  ┌─────┐ ┌─────┐ ┌─────┐                                   │
│  │ [1] │ │ [2] │ │ [3] │    Thumbnail navigation           │
│  └─────┘ └─────┘ └─────┘                                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    [⬇️ Download]  [Close]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Preview Features:**
- Navigate between slides with arrows or thumbnails
- Keyboard navigation (← →)
- Zoom capability for detailed view
- Direct download from preview

### 4.4 Download PowerPoint

**User Action:** Click "Download" button

**System Response:**
1. Download initiates immediately
2. Browser handles file download
3. Toast: "Downloading Q4_Revenue_Analysis.pptx..."

### 4.5 Delete PowerPoint

**User Action:** Click "Delete" button

**Confirmation Dialog:**
```
┌─────────────────────────────────────────────────────────────┐
│  Delete PowerPoint                                    [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ Are you sure you want to delete this file?             │
│                                                             │
│     📽️ Q4_Revenue_Analysis.pptx (1.2 MB)                   │
│                                                             │
│  This action cannot be undone.                             │
│                                                             │
│                           [Cancel]  [🗑️ Delete]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.6 Empty State - PowerPoints

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                      ┌───────────┐                          │
│                      │    📽️     │                          │
│                      │   ────    │                          │
│                      └───────────┘                          │
│                                                             │
│           No PowerPoints generated yet                      │
│                                                             │
│    Generate presentations from your Data Cards in          │
│         Chat with Data to find them here.                   │
│                                                             │
│                 [Go to Chat with Data]                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# Module: Settings

## 5. Entry Point: Settings Screen

### 5.1 Accessing Settings

**Method 1: Navigation Menu**
- Click "Settings" in the main navigation sidebar

**Method 2: User Profile**
- Click user avatar in header → Select "Settings" from dropdown

**System Response:**
- Settings page loads with default section (Account Details)
- Left sidebar shows settings categories

### 5.2 Settings Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Header Bar                                                      │
│  [≡ Menu]  Settings                              [👤 User Name] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┬──────────────────────────────────────────┐    │
│  │              │                                           │    │
│  │  Settings    │  Account Details                         │    │
│  │  ──────────  │  ────────────────────────────────────    │    │
│  │              │                                           │    │
│  │  👤 Account  │  [Content Area]                          │    │
│  │              │                                           │    │
│  │  💳 Plan &   │                                           │    │
│  │     Billing  │                                           │    │
│  │              │                                           │    │
│  │  🔒 Password │                                           │    │
│  │              │                                           │    │
│  │  ──────────  │                                           │    │
│  │              │                                           │    │
│  │  🚪 Logout   │                                           │    │
│  │              │                                           │    │
│  └──────────────┴──────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Settings Navigation

| Section | Icon | Description |
|---------|------|-------------|
| Account | 👤 | Profile information management |
| Plan & Billing | 💳 | Subscription, credits, payments |
| Password | 🔒 | Change password |
| Logout | 🚪 | Sign out of account |

---

## 6. Account Details Management

### 6.1 View Account Details

**Default View:**
```
┌─────────────────────────────────────────────────────────────┐
│  Account Details                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Profile Information                              [✏️ Edit] │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌───────┐                                                  │
│  │       │  John Doe                                        │
│  │  👤   │  john.doe@email.com                              │
│  │       │  Member since: January 2025                      │
│  └───────┘                                                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  First Name       │  John                           │   │
│  │  ─────────────────┼─────────────────────────────────│   │
│  │  Last Name        │  Doe                            │   │
│  │  ─────────────────┼─────────────────────────────────│   │
│  │  Email            │  john.doe@email.com (verified)  │   │
│  │  ─────────────────┼─────────────────────────────────│   │
│  │  Account Created  │  January 1, 2025                │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Edit First Name & Last Name

**User Action:** Click "Edit" button

**System Response:**

**Edit Mode:**
```
┌─────────────────────────────────────────────────────────────┐
│  Account Details                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Profile Information                           [Cancel]     │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  First Name *                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ John                                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Last Name *                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Doe                                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Email (cannot be changed)                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ john.doe@email.com                          🔒       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                                        [Save Changes]       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Field Validation:**

| Field | Validation | Error Message |
|-------|------------|---------------|
| First Name | Required, 2-50 characters | "First name is required" / "Must be 2-50 characters" |
| Last Name | Required, 2-50 characters | "Last name is required" / "Must be 2-50 characters" |

**User Action:** Make changes and click "Save Changes"

**System Response:**
1. Validation runs
2. If valid: Loading spinner on button
3. Success: Toast "Profile updated successfully"
4. Return to view mode with updated information

---

## 7. Subscription & Payment Management

### 7.1 Plan & Billing Overview

**User Action:** Click "Plan & Billing" in settings sidebar

**Screen Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Plan & Billing                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Current Plan                                               │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  ⭐ Pro Plan                              $29/month │   │
│  │                                                      │   │
│  │  ✓ 100 credits per month                            │   │
│  │  ✓ Unlimited data sources                           │   │
│  │  ✓ Advanced visualizations                          │   │
│  │  ✓ Priority support                                 │   │
│  │                                                      │   │
│  │  Next billing date: February 1, 2025                │   │
│  │                                                      │   │
│  │         [Change Plan]  [Unsubscribe]                │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Credit Balance                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │     💰 42 Credits Remaining                         │   │
│  │                                                      │   │
│  │     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░  42/100 used       │   │
│  │                                                      │   │
│  │     Resets on: February 1, 2025                     │   │
│  │                                                      │   │
│  │              [Buy Additional Credits]               │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 View Plan Details

**Information Displayed:**
- Plan name and tier
- Monthly price
- Plan features list
- Next billing date
- Action buttons

### 7.3 View Credit Balance

**Information Displayed:**
- Current credit count
- Visual progress bar (credits used vs. total)
- Reset date
- Buy credits action

**Credit Status Indicators:**

| Status | Visual | Threshold |
|--------|--------|-----------|
| Healthy | Green bar | > 50% remaining |
| Moderate | Yellow bar | 20-50% remaining |
| Low | Orange bar | 5-20% remaining |
| Critical | Red bar | < 5% remaining |

### 7.4 Buy Additional Credits

**User Action:** Click "Buy Additional Credits"

**System Response:**

**Credit Purchase Modal:**
```
┌─────────────────────────────────────────────────────────────┐
│  Buy Additional Credits                               [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Select Credit Package                                      │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │                     │  │                     │          │
│  │   💰 25 Credits     │  │   💰 50 Credits     │          │
│  │      $5.00          │  │      $9.00          │          │
│  │   $0.20/credit      │  │   $0.18/credit      │          │
│  │                     │  │                     │          │
│  │      [Select]       │  │      [Select]       │          │
│  │                     │  │                     │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │                     │  │                     │          │
│  │   💰 100 Credits    │  │   💰 250 Credits    │          │
│  │      $15.00         │  │      $35.00         │          │
│  │   $0.15/credit      │  │   $0.14/credit      │          │
│  │   ⭐ Most Popular   │  │   🏆 Best Value     │          │
│  │      [Select]       │  │      [Select]       │          │
│  │                     │  │                     │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  Note: Purchased credits do not expire and carry over      │
│  between billing cycles.                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User Action:** Select a package

**Payment Flow:**
```
┌─────────────────────────────────────────────────────────────┐
│  Complete Purchase                                    [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Order Summary                                              │
│  ─────────────────────────────────────────────────────────  │
│  100 Credits                                      $15.00   │
│  ─────────────────────────────────────────────────────────  │
│  Total                                            $15.00   │
│                                                             │
│  Payment Method                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ○ 💳 Visa ending in 4242 (default)                        │
│  ○ 💳 Add new card                                          │
│                                                             │
│                                                             │
│                    [Cancel]  [💳 Pay $15.00]               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Success State:**
```
┌─────────────────────────────────────────────────────────────┐
│  Purchase Complete                                    [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                      ┌───────────┐                          │
│                      │    ✓     │                          │
│                      └───────────┘                          │
│                                                             │
│              100 credits added to your account!             │
│                                                             │
│         New balance: 142 credits                            │
│                                                             │
│         Receipt sent to: john.doe@email.com                │
│                                                             │
│                        [Done]                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Error Handling:**

| Error | Message | Action |
|-------|---------|--------|
| Payment declined | "Payment failed. Please check your card details." | Retry or use different card |
| Network error | "Connection error. Please try again." | Retry button |
| Card expired | "Your card has expired. Please update payment method." | Add new card |

### 7.5 Unsubscribe

**User Action:** Click "Unsubscribe" button

**System Response:**

**Confirmation Dialog - Step 1:**
```
┌─────────────────────────────────────────────────────────────┐
│  Unsubscribe                                          [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  😢 We're sorry to see you go!                             │
│                                                             │
│  Before you leave, please tell us why:                     │
│                                                             │
│  ○ Too expensive                                           │
│  ○ Not using it enough                                     │
│  ○ Missing features I need                                 │
│  ○ Found a better alternative                              │
│  ○ Technical issues                                        │
│  ○ Other                                                   │
│                                                             │
│  Additional feedback (optional):                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                   [Keep Subscription]  [Continue]          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Confirmation Dialog - Step 2:**
```
┌─────────────────────────────────────────────────────────────┐
│  Confirm Unsubscription                               [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ Are you sure you want to unsubscribe?                  │
│                                                             │
│  If you unsubscribe:                                       │
│  • Your access continues until February 1, 2025            │
│  • Remaining 42 credits will expire on that date           │
│  • Your saved reports and files will be retained           │
│  • You can resubscribe anytime                             │
│                                                             │
│  Type "UNSUBSCRIBE" to confirm:                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                [Cancel]  [Confirm Unsubscription]          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Success State:**
- Toast: "Your subscription has been cancelled"
- Plan section updates to show "Expires on [date]"
- Email confirmation sent

---

## 8. Password Management

### 8.1 Change Password

**User Action:** Click "Password" in settings sidebar

**Screen Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Change Password                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Update your password to keep your account secure.         │
│                                                             │
│  Current Password *                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ••••••••••••                               [👁️]     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  New Password *                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                             [👁️]     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Password Requirements:                                     │
│  ☐ At least 8 characters                                   │
│  ☐ Contains uppercase letter                               │
│  ☐ Contains lowercase letter                               │
│  ☐ Contains a number                                       │
│  ☐ Contains special character (!@#$%^&*)                   │
│                                                             │
│  Confirm New Password *                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                             [👁️]     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                                    [Update Password]        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Password Requirements (Real-time Validation):**
- Requirements checklist updates as user types
- ✓ Green checkmark when requirement met
- ☐ Empty checkbox when not met

**Field Validation:**

| Field | Validation | Error Message |
|-------|------------|---------------|
| Current Password | Required, must match | "Current password is incorrect" |
| New Password | Must meet all requirements | "Password does not meet requirements" |
| Confirm Password | Must match new password | "Passwords do not match" |

**User Action:** Complete form and click "Update Password"

**System Response:**
1. Validation runs
2. Loading state on button
3. Success: Toast "Password updated successfully"
4. Form clears
5. Optional: Email notification sent

**Error States:**

| Error | Display |
|-------|---------|
| Wrong current password | Inline error below field |
| Weak new password | Requirements not met highlighted in red |
| Passwords don't match | Inline error below confirm field |
| Same as current | "New password must be different from current" |

---

## 9. Logout

### 9.1 Logout Flow

**User Action:** Click "Logout" in settings sidebar

**System Response:**

**Confirmation Dialog:**
```
┌─────────────────────────────────────────────────────────────┐
│  Logout                                               [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🚪 Are you sure you want to logout?                       │
│                                                             │
│  You will be redirected to the login page.                 │
│                                                             │
│                        [Cancel]  [Logout]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**User Action:** Click "Logout"

**System Response:**
1. Session cleared
2. Loading indicator briefly
3. Redirect to login page
4. Toast on login page: "You have been logged out"

---

## 10. Error Handling Summary

### 10.1 Collections Module Errors

| Scenario | Error Message | Recovery Action |
|----------|---------------|-----------------|
| File not found | "File no longer exists." | Refresh list |
| Download fails | "Download failed. Please try again." | Retry button |
| Delete fails | "Could not delete. Please try again." | Retry button |

### 10.2 Settings Module Errors

| Scenario | Error Message | Recovery Action |
|----------|---------------|-----------------|
| Profile update fails | "Could not save changes. Please try again." | Retry |
| Payment fails | "Payment declined. Please try another card." | Add new card |
| Password change fails | "Could not update password. Please try again." | Retry |
| Session expired | "Session expired. Please login again." | Redirect to login |

---

## 11. Accessibility Considerations

### 11.1 Keyboard Navigation

| Action | Shortcut |
|--------|----------|
| Navigate settings sections | Tab / Arrow keys |
| Activate buttons | Enter / Space |
| Close modals | Escape |
| Toggle password visibility | Enter on eye icon |

### 11.2 Screen Reader Support

- All form fields have associated labels
- Error messages announced when they appear
- Modal dialogs trap focus appropriately
- Action confirmations announced

---

## 12. Mobile Responsiveness

### 12.1 Collections on Mobile

- Tab bar becomes horizontally scrollable
- File list switches to card view
- Actions accessible via swipe or long-press

### 12.2 Settings on Mobile

- Sidebar collapses to top navigation or hamburger menu
- Forms stack vertically
- Modals become full-screen sheets
- Touch-friendly input sizes (min 44px)

---

## Appendix A: Component Specifications

### A.1 File Card Component

| Property | Type | Description |
|----------|------|-------------|
| fileName | string | Display name |
| fileType | string | CSV, XLSX, JSON, etc. |
| fileSize | number | Size in bytes |
| uploadDate | datetime | Upload timestamp |
| onDownload | function | Download handler |
| onDelete | function | Delete handler |

### A.2 Credit Display Component

| Property | Type | Description |
|----------|------|-------------|
| current | number | Current credit balance |
| total | number | Total credits for period |
| resetDate | date | When credits reset |
| status | enum | healthy, moderate, low, critical |

---

## Appendix B: Animation Specifications

| Interaction | Animation | Duration | Easing |
|-------------|-----------|----------|--------|
| Tab switch | Fade + slide | 200ms | ease-out |
| Modal open | Fade + scale up | 250ms | ease-out |
| Modal close | Fade + scale down | 200ms | ease-in |
| File delete | Fade + collapse | 300ms | ease-in-out |
| Toast appear | Slide in from top | 300ms | ease-out |
| Progress bar | Width transition | 500ms | ease-in-out |
