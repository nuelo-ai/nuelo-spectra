# **Spectra Product Overview**

Spectra is an AI-powered data analytics platform that transforms how users interact with their data. By combining intuitive file management with natural language processing, Spectra enables anyone—regardless of technical expertise—to upload datasets, ask questions in plain English, and receive instant insights, visualizations, and exportable reports.

## What Spectra Does

Spectra bridges the gap between raw data and actionable insights. Users upload their Excel or CSV files, and the platform's AI engine automatically interprets the data structure, suggests relevant analyses, and allows users to explore their data through a conversational chat interface. Results are presented as interactive "Data Cards" containing tables, explanations, and visualizations that can be saved, shared, or exported to PowerPoint.

## Key Features

**Flexible Authentication**
Secure account access via email registration with verification or seamless Google OAuth sign-in. Includes password recovery, rate limiting, and account security protections.

**Smart File Upload & AI Interpretation**
Drag-and-drop support for Excel and CSV files up to 50MB. The platform automatically analyzes data structure, identifies column types, and generates a natural language summary of what the data contains—with options for users to refine the AI's understanding.

**Conversational Data Analysis (Chat with Data)**
Ask questions about your data in natural language. The system generates and executes Python scripts in a secure sandbox, returning results as Data Cards with query summaries, sortable tables, AI-generated explanations, and interactive charts.

**Data Cards with Export Options**
Analysis results are packaged into shareable Data Cards. Export options include PowerPoint slides, PDF documents, PNG images, and CSV data files. Users can save cards to their collections for future reference.

**Centralized Collections Management**
A unified hub for managing uploaded files, saved reports, and generated presentations. Supports bulk operations including multi-file download and deletion.

**Credit-Based Usage Model**
Transparent credit tracking with balance indicators, low-credit warnings, and subscription management through the Settings module.

**Enterprise-Grade Security**
Password hashing with bcrypt/Argon2, HTTPS encryption, CSRF protection, session management, and comprehensive audit logging. GDPR and CCPA compliant data handling.

**Accessibility & Responsive Design**
WCAG 2.1 AA compliant interfaces with full keyboard navigation, screen reader support, and mobile-responsive layouts optimized for tablets and smartphones.

---

*Spectra: Turn your data into decisions through the power of conversation.*


# **1\. Authentication**

## Overview

The **Authentication** section outlines the user flows, edge cases, and security considerations for two primary methods of accessing the Spectra platform: **Sign Up/Login using Email** and **Sign Up/Login using Google Account (OAuth)**.

## Key Flows

1. **Sign Up Using Email**: Users create an account with an email and password, requiring email verification before full access.  
2. **Sign Up Using Google Account**: Users leverage Google OAuth for quick sign-up, automatically setting the account to "verified."  
3. **Login Using Email**: Standard email and password login with validation, failed attempt counters, and email verification checks.  
4. **Login Using Google Account**: Uses OAuth to verify identity and log the user into an existing, linked account.  
5. **Forgot Password**: Provides a secure process via email-sent, expiring links for users to reset their password.

## Core Requirements

* **Security**: Strong hashing (e.g., bcrypt), HTTPS, CSRF protection, rate limiting, and account lockout for security.  
* **Verification**: Email verification is mandatory for email-registered accounts.  
* **Edge Cases**: Detailed handling for scenarios like registered emails, failed validation, expired links, and account locking.  
* **UX**: Clear error messages, password strength indicators, mobile responsiveness, and accessible forms are required.

## 1\. Sign Up Using Email

### User Flow

1. User navigates to the sign-up page  
2. User clicks "Sign up with Email" button  
3. System displays sign-up form with the following fields:  
   - Email address (required)  
   - Password (required, with strength indicator)  
   - Confirm Password (required)  
   - Full Name (required)  
   - Accept Terms and Conditions checkbox (required)  
4. User fills in all required fields  
5. User clicks "Create Account" button  
6. System validates inputs:  
   - Email format is valid  
   - Email is not already registered  
   - Password meets minimum requirements (e.g., 8+ characters, mix of letters and numbers)  
   - Passwords match  
   - Terms and Conditions are accepted  
7. If validation fails, system displays error messages next to relevant fields  
8. If validation passes:  
   - System creates user account with "unverified" status  
   - System sends verification email to the provided address  
   - System displays confirmation message: "Account created\! Please check your email to verify your account"  
9. User receives verification email with a unique link  
10. User clicks verification link  
11. System verifies the token and marks account as "verified"  
12. System redirects user to login page or automatically logs user in  
13. System displays success message: "Email verified successfully\!"

### Edge Cases

- User tries to sign up with an already registered email → Display: "This email is already registered. Please log in or use a different email"  
- Verification email not received → Provide "Resend verification email" option  
- Verification link expires (e.g., after 24 hours) → Display error and offer to resend verification email

---

## 2\. Sign Up Using Google Account

### User Flow

1. User navigates to the sign-up page  
2. User clicks "Sign up with Google" button  
3. System redirects to Google OAuth consent screen  
4. User selects or enters their Google account credentials  
5. Google displays permission request for profile information (email, name, profile picture)  
6. User clicks "Allow" to grant permissions  
7. Google redirects back to application with authorization code  
8. System exchanges authorization code for user information  
9. System checks if Google email is already registered:  
   - If yes → Log user in and redirect to dashboard  
   - If no → Continue with account creation  
10. System creates new account with:  
    - Email from Google profile  
    - Name from Google profile  
    - Profile picture from Google (optional)  
    - Account status automatically set to "verified"  
    - OAuth provider marked as "Google"  
11. System creates user session  
12. System redirects user to onboarding flow or dashboard  
13. System displays welcome message

### Edge Cases

- User cancels Google authorization → Return to sign-up page with message: "Sign-up cancelled"  
- Google account email already registered via email sign-up → Prompt user to link accounts or log in with email  
- Google OAuth service unavailable → Display error message and suggest email sign-up alternative

---

## 3\. Login Using Email

### User Flow

1. User navigates to login page  
2. User enters credentials:  
   - Email address  
   - Password  
3. User clicks "Log In" button  
4. System validates credentials:  
   - Email exists in database  
   - Password matches stored hash  
5. If validation fails:  
   - System displays error: "Invalid email or password"  
   - System increments failed login attempt counter  
   - After 5 failed attempts, implement rate limiting or CAPTCHA  
6. If validation passes:  
   - System checks if email is verified  
   - If not verified → Display: "Please verify your email address" with option to resend verification  
7. If account is verified:  
   - System creates user session/JWT token  
   - System records login timestamp and device information  
   - System redirects user to dashboard  
8. Optional: If "Remember Me" checkbox is selected, create long-lived session

### Edge Cases

- Account locked due to too many failed attempts → Display lockout message with timeframe or contact support option  
- User account has been deactivated → Display: "Account deactivated. Contact support for assistance"  
- Concurrent sessions → Handle based on security policy (allow, limit, or require logout from other devices)

---

## 4\. Login Using Google Account

### User Flow

1. User navigates to login page  
2. User clicks "Continue with Google" button  
3. System redirects to Google OAuth consent screen  
4. User selects their Google account or enters credentials  
5. Google redirects back with authorization code  
6. System exchanges code for Google user information  
7. System checks if Google email exists in database:  
   - If yes → Continue to step 8  
   - If no → Display: "No account found. Please sign up first" and redirect to sign-up page  
8. System verifies account is linked to Google OAuth  
9. System creates user session/JWT token  
10. System records login timestamp and device information  
11. System redirects user to dashboard

### Edge Cases

- User cancels Google authorization → Return to login page  
- Google email exists but was registered via email (not OAuth) → Offer to link Google account to existing account with email verification  
- Google OAuth service unavailable → Display error and suggest email login alternative  
- User's Google account access revoked → Clear OAuth tokens and require re-authentication

---

## 5\. Forgot Password

### User Flow

1. User navigates to login page  
2. User clicks "Forgot Password?" link  
3. System displays password reset page with email input field  
4. User enters their registered email address  
5. User clicks "Send Reset Link" button  
6. System validates email:  
   - Email format is correct  
   - Email exists in database  
7. If email is valid:  
   - System generates unique password reset token with expiration (e.g., 1 hour)  
   - System sends password reset email with reset link  
   - System displays message: "If an account exists with this email, you will receive password reset instructions"  
   - Note: Display same message whether email exists or not (security best practice)  
8. User receives password reset email  
9. User clicks reset link in email  
10. System validates reset token:  
    - Token exists and hasn't expired  
    - Token hasn't been used already  
11. If token is valid:  
    - System displays password reset form with fields:  
      - New Password (with strength indicator)  
      - Confirm New Password  
12. User enters new password twice  
13. User clicks "Reset Password" button  
14. System validates:  
    - Password meets requirements  
    - Passwords match  
    - New password is different from old password (optional)  
15. If validation passes:  
    - System updates password with new hash  
    - System invalidates reset token  
    - System invalidates all existing sessions (optional security measure)  
    - System displays success message: "Password reset successful"  
    - System redirects to login page  
16. User logs in with new password

### Edge Cases

- Reset link expired → Display: "Reset link expired. Please request a new one" with link to forgot password page  
- Token already used → Display: "Reset link already used. Please request a new one"  
- User requests multiple reset emails → Only most recent token is valid, previous tokens are invalidated  
- Account registered via Google OAuth (no password) → Display: "This account uses Google sign-in. Please log in with Google"

---

## General Security Considerations

- All passwords stored using strong hashing algorithm (e.g., bcrypt, Argon2)  
- HTTPS/SSL encryption for all authentication endpoints  
- CSRF protection on all forms  
- Rate limiting on login and password reset endpoints  
- Session timeout after period of inactivity  
- Secure password requirements enforced  
- Account lockout after multiple failed login attempts  
- Email verification required before full account access  
- Audit logging for all authentication events

## UI/UX Considerations

- Clear error messages without exposing security information  
- Loading states during authentication process  
- Accessible forms with proper labels and ARIA attributes  
- Mobile-responsive design  
- Clear call-to-action buttons  
- Progress indicators for multi-step processes  
- Option to show/hide password  
- Password strength indicator during account creation

# **2\. File Upload**

## Overview

The **Add Data Source \- File Upload Flow** section outlines the end-to-end process for users to upload a file (primarily Excel or CSV) to the Spectra platform, turning it into an interactive data source.

## Key Stages:

1. **Initiation (Steps 1-3):** User logs in, navigates to the Dashboard, and initiates the process by clicking "Upload Data," which triggers a modal.  
2. **Form Completion (Step 4):** User provides mandatory details: **Dataset Name** (unique within project) and the **File** (max 50MB, .xlsx/.xls/.csv formats). An optional **Data Context** description aids AI interpretation.  
3. **Preprocessing (Step 5):** The file is uploaded and processed server-side (upload, validation, analysis, AI interpretation). A progress indicator (0-100%) and a "Cancel Processing" option are provided.  
4. **Success & Review (Step 6-7):** Upon success, a summary screen appears, displaying **Data Summary Statistics** (rows, columns), a **Sample Data Preview**, and an **AI Interpretation** (a natural language summary and suggested use cases). Users can **Continue** (accept), **Edit Understanding** (provide clarification), or **Skip for Now**.  
5. **Failure & Recovery (Step 8):** If preprocessing fails (e.g., invalid structure, corrupted file), a dedicated error screen provides an **Error Message** (specific and actionable), links to **Helpful Resources**, and options to **Try Different File** or **Cancel**.  
6. **Completion (Step 9-10):** A successful upload closes the modal, triggers a success notification, updates the Dashboard, and opens a new **Data Source Tab** where users can interact with the data via **AI-Suggested Actions** and a **Custom Query/Action Area**.

---

## 1\. User Authentication & Dashboard Access

### User Flow

1. User navigates to the platform login page  
2. User completes authentication (via email or Google OAuth)  
3. System validates credentials and creates user session  
4. System redirects user to the main Dashboard

### Success State

- User is successfully authenticated  
- Dashboard loads with user's projects and data sources

---

## 2\. Dashboard Overview

### Initial State

1. Dashboard displays upon successful login  
2. System checks for existing projects:  
   - If user has no projects → System automatically creates a "Default" project  
   - If user has existing projects → Display all projects  
3. "Default" project is visible and accessible to the user

### Default Project Structure

- **Name**: "Default" (system-generated)  
- **Contains**: Multiple data sources (files uploaded by user)  
- **Purpose**: Groups related data sources together for organizational purposes  
- Note: For current implementation, projects contain only data sources (reports and other features to be added later)

### Dashboard Components

- Project list/cards showing available projects  
- "Upload Data" button (primary action button)  
- Navigation menu  
- Project overview metrics (number of data sources, last updated, etc.)

---

## 3\. Initiating File Upload

### User Flow

1. User identifies the "Upload Data" button on the dashboard  
2. User clicks the "Upload Data" button  
3. System triggers modal overlay  
4. Modal view appears on screen, dimming the background dashboard

### Modal Appearance

- Modal centered on screen  
- Semi-transparent background overlay  
- Modal title: "Upload New Data Source"  
- Close button (X) in top-right corner

---

## 4\. Data Upload Modal \- Form Completion

### Modal Components & Fields

#### Field 1: Name of the Dataset (Mandatory)

- **Label**: "Dataset Name\*"  
- **Type**: Text input  
- **Validation**:  
  - Cannot be empty  
  - Minimum 3 characters  
  - Maximum 100 characters  
  - Must be unique within the project  
- **Placeholder**: "e.g., Q4 Sales Data 2024"  
- **Helper Text**: "Enter a descriptive name to identify this dataset"  
- **Error Messages**:  
  - "Dataset name is required"  
  - "Name must be at least 3 characters"  
  - "A dataset with this name already exists"

#### Field 2: Context of the File (Optional)

- **Label**: "Data Context"  
- **Type**: Text area (multi-line input)  
- **Validation**:  
  - Optional field  
  - Maximum 500 characters  
- **Placeholder**: "e.g., This file contains quarterly sales data broken down by product category, region, and sales representative"  
- **Helper Text**: "Describe what this data contains. This helps our AI better understand and analyze your data"  
- **Character Counter**: Shows remaining characters (e.g., "450/500 characters remaining")

#### Field 3: Upload File (Mandatory)

- **Label**: "Upload File\*"  
- **Type**: File upload (drag-and-drop or file selector)  
- **Accepted Formats**:  
  - Excel files (.xlsx, .xls)  
  - CSV files (.csv) \- if supported  
- **Maximum File Size**: 50MB (configurable)  
- **Upload Options**:  
  - **Drag & Drop Zone**:  
    - Dashed border rectangle  
    - Upload icon  
    - Text: "Drag and drop your Excel file here"  
    - "or" divider  
    - "Browse Files" button  
  - **File Browser**: Opens native file selection dialog  
- **File Preview**: Once file is selected:  
  - Display file name  
  - Display file size  
  - Display file icon/thumbnail  
  - "Remove" or "Change File" button to reselect  
- **Validation**:  
  - File format must be supported  
  - File size must not exceed limit  
  - File must not be corrupted  
- **Error Messages**:  
  - "Please upload a file"  
  - "File format not supported. Please upload .xlsx or .xls file"  
  - "File size exceeds 50MB limit"  
  - "File appears to be corrupted. Please try another file"

#### Action Buttons

**Submit Button**

- **Label**: "Upload and Process"  
- **Type**: Primary button  
- **State**:  
  - Disabled until all mandatory fields are filled  
  - Enabled when Dataset Name and File are provided  
- **Position**: Bottom right of modal  
- **Action**: Initiates file upload and preprocessing

**Cancel Button**

- **Label**: "Cancel"  
- **Type**: Secondary button (outline or text button)  
- **Position**: Bottom right, left of Submit button  
- **Action**:  
  - Closes modal without saving  
  - Discards all entered information  
  - Returns user to dashboard  
- **Confirmation**: If user has entered data, show confirmation dialog:  
  - "Are you sure you want to cancel? All entered information will be lost."  
  - Options: "Yes, Cancel" or "No, Continue Editing"

### User Interaction Flow

1. User enters dataset name in the text input  
2. User optionally adds context description  
3. User uploads file via:  
   - **Option A**: Drag file from computer and drop into upload zone  
   - **Option B**: Click "Browse Files" button, select file from file dialog  
4. System displays selected file details (name, size)  
5. User reviews all entered information  
6. User clicks "Upload and Process" button  
7. Modal transitions to processing state

---

## 5\. Preprocessing \- Progress Indication

### Preprocessing Initiation

1. User clicks "Upload and Process" button  
2. Modal content changes to show processing state  
3. System begins file upload and preprocessing in background

### Processing Modal Components

- **Progress Bar**:  
  - Animated progress indicator (0-100%)  
  - Color: Primary brand color  
  - Smooth animation  
- **Status Text**:  
  - "Uploading file..." (0-30%)  
  - "Processing data..." (30-70%)  
  - "Analyzing structure..." (70-100%)  
- **Processing Steps Indicator** (optional):  
  - ✓ Uploading file  
  - ⟳ Validating data structure  
  - ⟳ Analyzing columns and rows  
  - ⟳ Generating insights  
- **Cancel Button**:  
  - "Cancel Processing" option  
  - Confirmation: "Are you sure you want to stop processing? Uploaded data will be discarded."

### Background Processing Steps

1. **File Upload** (0-30%):  
   - Upload file to server  
   - Verify file integrity  
2. **Data Validation** (30-50%):  
   - Check file format compliance  
   - Validate against data model requirements  
   - Check for corrupted data  
3. **Data Analysis** (50-70%):  
   - Count rows and columns  
   - Identify data types for each column  
   - Extract sample data (first 10-20 rows)  
   - Detect headers and column names  
4. **AI Interpretation** (70-100%):  
   - Send data context \+ sample data to AI  
   - Generate natural language interpretation  
   - Create suggested actions based on data type

### Processing Duration

- Typical processing time: 10-60 seconds  
- Depends on file size and complexity  
- System displays estimated time remaining (if calculable)

---

## 6\. Preprocessing Success \- Data Summary & AI Interpretation

### Success State Transition

1. Preprocessing completes successfully (100%)  
2. Modal transitions from processing view to summary view  
3. Success animation or checkmark briefly displayed  
4. New screen content loads within the modal

### Summary Screen Components

#### Section 1: Data Summary Statistics

**Header**: "Data Summary"

**Metrics Display** (Card or Table Layout):

- **Total Rows**: "1,250 rows"  
  - Icon: Table rows icon  
  - Description: Total number of data records  
- **Total Columns**: "8 columns"  
  - Icon: Table columns icon  
  - Description: Number of data fields/attributes  
- **File Size**: "2.3 MB"  
- **Upload Date**: Current timestamp  
- **Column Names List**: Display all column headers  
  - Example: "Product Name, Category, Price, Quantity, Sales Date, Region, Sales Rep, Revenue"

#### Section 2: Sample Data Preview

**Header**: "Data Preview"

**Table View**:

- Display first 5-10 rows of data  
- Show all columns with headers  
- Scrollable if data exceeds viewport  
- Styled as data table with alternating row colors  
- Column headers in bold  
- Responsive design for mobile viewing

**Example Table**:
```
| Product Name | Category    | Price  | Quantity | Sales Date | Region    | Sales Rep    | Revenue   |
|--------------|-------------|--------|----------|------------|-----------|--------------|-----------|
| Widget A     | Electronics | $49.99 | 120      | 2024-01-15 | Northeast | John Smith   | $5,998.80 |
| Widget B     | Home Goods  | $29.99 | 85       | 2024-01-16 | Southwest | Jane Doe     | $2,549.15 |
| ...          | ...         | ...    | ...      | ...        | ...       | ...          | ...       |
```

**Table Features**:

- Column sorting (optional)  
- "View Full Dataset" link (opens expanded view)

#### Section 3: AI Interpretation

**Header**: "AI Understanding"

**AI-Generated Insight Card**:

- **Icon**: AI/sparkle icon  
- **Background**: Subtle highlight color to distinguish from other sections  
- **Content**: Natural language interpretation based on:  
  - Dataset name  
  - Data context (if provided by user)  
  - Column names and data types  
  - Sample data values

**Example AI Interpretation**:

*"Based on your dataset, this appears to contain product sales information with* 

*detailed transactional data. The data includes:*

*• Product catalog with pricing information*

*• Sales transactions across multiple regions (Northeast, Southwest, etc.)*

*• Sales performance tracked by individual sales representatives*

*• Time-series data spanning from January to March 2024*

*• Revenue calculations and quantity metrics*

*This dataset is well-suited for:*

*\- Sales trend analysis by product category or region*

*\- Individual sales representative performance tracking*

*\- Revenue forecasting and predictive analytics*

*\- Seasonal sales pattern identification"*

**AI Interpretation Features**:

- Bullet points for clarity  
- Highlights key data attributes  
- Suggests potential use cases  
- Uses user's provided context to enhance accuracy  
- Natural, conversational tone

#### Section 4: User Actions

**Action Buttons** (Three Options):

**Option 1: Continue Button**

- **Label**: "Continue"  
- **Type**: Primary button  
- **Icon**: Checkmark or arrow right  
- **Action**:  
  - Saves the dataset with all provided information  
  - Associates AI interpretation with the data source  
  - Marks data as "AI understanding accepted by user"  
  - Closes modal  
  - Redirects to dashboard with new data source tab  
  - Shows success notification: "Dataset '\[Name\]' uploaded successfully"

**Option 2: Edit Button**

- **Label**: "Edit Understanding"  
- **Type**: Secondary button  
- **Icon**: Edit/pencil icon  
- **Action**:  
  - Expands an editable text area below AI interpretation  
  - Allows user to provide clarification in natural language  
  - Does not immediately close modal  
  - Triggers "Save Clarification" flow

**Option 3: Skip Button**

- **Label**: "Skip for Now"  
- **Type**: Tertiary button or text link  
- **Action**:  
  - Saves dataset without AI interpretation confirmation  
  - Marks as "User skipped AI review"  
  - Closes modal  
  - Redirects to dashboard  
  - Can revisit AI interpretation later from data source settings

### Button Layout

\[Skip for Now\]                    \[Edit Understanding\]  \[Continue →\]

---

## 7\. Edit Understanding Flow (Clarification)

### User Flow

1. User clicks "Edit Understanding" button  
2. System expands a text input area below the AI interpretation section  
3. Modal remains open with additional content visible

### Clarification Interface

#### Components

**Instructional Text**:

- "Help us better understand your data by providing clarifications or corrections below:"

**Text Input Area**:

- **Type**: Multi-line text area  
- **Placeholder**: "e.g., This data actually focuses on B2B sales only, not retail. The 'Region' column refers to sales territories, not geographic regions. Product categories should be grouped differently..."  
- **Character Limit**: 1000 characters  
- **Character Counter**: Displayed below input  
- **Helper Text**: "Describe any corrections or additional context that would help our AI better understand your data"

**Original AI Interpretation** (for reference):

- Remains visible above the input area  
- Marked as "Original Understanding" or similar label  
- Slightly dimmed or in a collapsed/minimized state

**Action Buttons**:

**Save Button**:

- **Label**: "Save Clarification"  
- **Type**: Primary button  
- **State**:  
  - Disabled if text area is empty  
  - Enabled when user enters text  
- **Action**:  
  - Saves user's clarification text  
  - Sends clarification \+ original data to AI for reprocessing  
  - Shows brief loading state (3-10 seconds)  
  - Generates updated AI interpretation  
  - Returns to previous summary screen with updated interpretation  
  - Highlights the updated interpretation  
  - Shows notification: "AI understanding updated based on your feedback"

**Cancel Edit Button**:

- **Label**: "Cancel"  
- **Type**: Secondary button  
- **Action**:  
  - Collapses clarification input area  
  - Discards unsaved text  
  - Returns to previous view with original AI interpretation  
  - No data is lost

### Clarification Processing Flow

1. User enters clarification text  
2. User clicks "Save Clarification"  
3. System shows inline loading indicator: "Updating understanding..."  
4. System processes:  
   - Combines user clarification with original data context  
   - Sends to AI for re-interpretation  
   - Generates new, refined interpretation  
5. System updates the AI interpretation section with new content  
6. System highlights changes or shows "Updated" badge  
7. User can review updated interpretation  
8. User can:  
   - Accept by clicking "Continue"  
   - Clarify again if still not accurate  
   - Skip if they prefer

### Data Association

**What Gets Saved**:

- Original user-provided data context (from upload modal)  
- User's clarification text (from edit flow)  
- Final AI interpretation (after any clarifications)  
- Timestamp of clarification  
- Version history (optional): Track original vs. clarified interpretations

**How It's Used**:

- Stored in database associated with the data source  
- Used as context for future AI queries on this dataset  
- Referenced when user asks questions or requests analysis  
- Can be edited/updated later from data source settings

---

## 8\. Preprocessing Failure \- Error Handling

### Failure Triggers

Preprocessing fails when:

- File does not conform to required data model  
- File structure is invalid (e.g., no headers, empty file)  
- File contains only non-tabular data  
- Data types are incompatible with platform requirements  
- File is corrupted or unreadable  
- File contains unsupported special characters or encoding

### Failure State Transition

1. During preprocessing (at any percentage)  
2. System detects non-conforming data or validation error  
3. Progress bar stops  
4. Error state is triggered  
5. Modal content changes to error screen

### Error Screen Components

#### Error Icon

- Red warning/alert icon  
- Clear visual indication of failure

#### Error Title

- **Text**: "Unable to Process File"  
- **Style**: Bold, prominent heading

#### Error Message

Specific, actionable error messages based on failure type:

**Example Error Messages**:

1. **Invalid File Structure**:  
     
   - "The uploaded file does not contain a valid data table. Please ensure your Excel file has:  
     - Headers in the first row  
     - Data starting from the second row  
     - At least one column of data"

   

2. **Data Model Mismatch**:  
     
   - "The file structure doesn't match our required data model. Expected columns: \[list expected columns\]. Found: \[list actual columns\]."

   

3. **Empty File**:  
     
   - "The uploaded file appears to be empty. Please upload a file with data."

   

4. **Corrupted File**:  
     
   - "The file appears to be corrupted and cannot be read. Please try:  
     - Re-saving the file in Excel  
     - Uploading a different copy  
     - Converting to .xlsx format"

   

5. **Encoding Issues**:  
     
   - "The file contains special characters or encoding that cannot be processed. Please save your file with UTF-8 encoding and try again."

   

6. **Size/Complexity Issues**:  
     
   - "The file is too complex to process. Please try:  
     - Splitting into smaller files  
     - Removing unnecessary columns or formatting  
     - Simplifying formulas or pivot tables"

#### Helpful Resources Section

- **Link**: "View Data Format Requirements" → Opens documentation  
- **Link**: "Download Sample Template" → Provides correctly formatted example file  
- **Support Contact**: "Need help? Contact support"

#### Action Buttons

**Try Again Button**:

- **Label**: "Try Different File"  
- **Type**: Primary button  
- **Action**:  
  - Returns user to upload modal (Step 4\)  
  - Retains dataset name and context (if user wants to keep them)  
  - Clears file selection  
  - User can upload a corrected file

**Cancel Button**:

- **Label**: "Cancel"  
- **Type**: Secondary button  
- **Action**:  
  - Closes modal  
  - Discards all progress  
  - Returns to dashboard  
  - No data source is created

**Edit Details Button** (Optional):

- **Label**: "Edit Details"  
- **Action**:  
  - Returns to upload modal  
  - Allows user to modify dataset name, context, or file  
  - Useful if user wants to adjust context before retrying

### Error Recovery Flow

1. User reads error message  
2. User understands what went wrong  
3. User has multiple options:  
   - **Fix file externally** → Download template, correct file, return to upload  
   - **Try different file** → Click "Try Different File", upload alternate file  
   - **Contact support** → Click support link for assistance  
   - **Cancel operation** → Click "Cancel", return to dashboard

### Error Logging

System logs the following for troubleshooting:

- Timestamp of failure  
- User ID  
- File name and size  
- Specific error type/code  
- Stack trace (if technical error)  
- User's dataset name and context  
- Available for admin review or support tickets

---

## 9\. Post-Upload Success \- Dashboard Redirect & Data Source Tab

### Success Completion Flow

1. User clicks "Continue" on summary screen  
2. Modal closes with fade-out animation  
3. Success notification appears (toast/banner):  
   - **Message**: "Dataset '\[Dataset Name\]' uploaded successfully\!"  
   - **Type**: Success (green checkmark)  
   - **Duration**: 3-5 seconds, auto-dismiss  
   - **Action**: Optional "Undo" or "View" button  
4. Dashboard updates to show new data source  
5. New tab opens representing the uploaded data source

### Dashboard Updates

**Project View Update**:

- "Default" project now shows updated data source count  
- Example: "3 data sources" (if 3 files uploaded)  
- Last updated timestamp refreshed

**Data Source Card** (if card view):

- New card appears in project  
- Card displays:  
  - Dataset name  
  - Upload date  
  - File size  
  - Row/column count  
  - Status: "Ready"  
  - Quick action buttons

---

## 10\. Data Source Tab Interface

### Tab Representation

A tab is opened to represent the newly uploaded data source. This tab allows the user to interact with and analyze the data.

### Tab Components

#### Tab Header

- **Tab Title**: Dataset name (e.g., "Q4 Sales Data 2024")  
- **Close Button**: X icon to close tab  
- **Tab Icon**: File/database icon  
- **Status Indicator**:  
  - Green dot \= Active/Ready  
  - Yellow dot \= Processing (if background tasks running)  
  - Red dot \= Error

#### Tab Content Area

**Section 1: Data Overview Panel** (Collapsible)

- Quick stats: Rows, columns, size  
- "View Full Data" button → Opens data table view  
- "Data Settings" button → Modify context, rename, delete

**Section 2: AI-Suggested Actions**

**Purpose**: Provide intelligent, contextual suggestions for what the user can do with their data

**Header**: "What would you like to do with this data?"

**Suggestion Cards** (3-5 suggestions displayed):

Each suggestion card contains:

- **Icon**: Relevant icon (chart, trend line, report, etc.)  
- **Title**: Action headline  
- **Description**: Brief explanation of what this action does  
- **Button**: "Try this" or action-specific CTA

#### How Suggestions Are Generated

- **AI Analysis**: Based on uploaded data structure, types, and context  
- **Column Detection**: Identifies key columns (dates, categories, metrics)  
- **Pattern Recognition**: Recognizes common data patterns (time series, categorical, numeric)  
- **Context-Aware**: Uses user's data context to refine suggestions  
- **Dynamic**: Different datasets generate different suggestions  
- **Prioritized**: Most relevant actions shown first

#### Suggestion Interaction Flow

1. User reviews suggested actions  
2. User clicks on a suggestion card (e.g., "Analyze Now")  
3. System navigates to appropriate tool/interface:  
   - Analysis tool opens  
   - Pre-populated with relevant data columns  
   - User can customize and run analysis  
4. Results displayed in new section or panel  
5. User can return to suggestions or continue with results

**Section 3: Custom Query/Action Area**

- **Search/Input Bar**: "Ask a question about your data..." or "What would you like to know?"  
- **Natural Language Processing**: User can type custom queries  
- **Examples**:  
  - "Show me the top 5 best-selling products"  
  - "What was the total revenue in Q3?"  
  - "Compare sales between regions"

**Section 4: Recent Activity/History** (Optional)

- Shows previously run analyses or generated reports  
- Quick access to return to previous work

---

## 11\. Edge Cases & Error Scenarios

### Edge Case 1: Duplicate Dataset Name

**Scenario**: User tries to upload a file with a name that already exists in the project

**Flow**:

1. User enters dataset name "Sales Data"  
2. Dataset "Sales Data" already exists in project  
3. On blur or submit, system validates  
4. Error message appears: "A dataset with this name already exists. Please choose a different name."  
5. Input field highlighted in red  
6. User must change name before proceeding

**Alternative**: System auto-suggests: "Sales Data (2)" or "Sales Data \- Copy"

### Edge Case 2: Network Interruption During Upload

**Scenario**: User's internet connection drops during file upload

**Flow**:

1. Upload/processing in progress  
2. Network disconnects  
3. Progress bar freezes or shows error state  
4. Error message: "Connection lost. Upload interrupted."  
5. Options:  
   - "Retry Upload" \- Resume from where it stopped (if supported)  
   - "Start Over" \- Begin upload from scratch  
   - "Cancel" \- Discard and return to dashboard

### Edge Case 3: Very Large File (Edge of Size Limit)

**Scenario**: User uploads 48MB file (near 50MB limit)

**Flow**:

1. File upload takes longer (30-60 seconds)  
2. Progress bar shows accurate percentage  
3. Status text: "Uploading large file... This may take a moment"  
4. Processing may take 60-120 seconds  
5. System displays estimated time: "Estimated time remaining: 1 minute"  
6. Success or timeout handling if processing exceeds threshold

### Edge Case 4: User Closes Browser During Processing

**Scenario**: User accidentally closes browser/tab while preprocessing

**Flow**:

1. Processing happens server-side  
2. On user's return to platform:  
   - If processing completed: Dataset appears in dashboard with "New" badge  
   - If processing failed: No dataset created, no error shown (clean slate)  
   - If still processing: Show in-progress indicator on dashboard  
3. Notification: "Your upload '\[Dataset Name\]' completed while you were away"

### Edge Case 5: Multiple Clarifications

**Scenario**: User is not satisfied with AI interpretation after first clarification

**Flow**:

1. User clicks "Edit Understanding" again  
2. Previous clarification text is pre-filled in text area  
3. User can edit or add to clarification  
4. User clicks "Save Clarification"  
5. System generates new interpretation (iteration 2\)  
6. User can repeat up to 3 times  
7. After 3 attempts: System suggests "Contact Support for specialized data modeling"

### Edge Case 6: File With No Headers

**Scenario**: User uploads Excel file without header row

**Flow**:

1. System detects no clear headers  
2. Error message: "No column headers detected. Please ensure your file has column names in the first row."  
3. Option 1: "Try Different File"  
4. Option 2: "Auto-generate headers" (if supported)  
   - System names columns: "Column 1", "Column 2", etc.  
   - User can rename later

### Edge Case 7: File With Merged Cells or Complex Formatting

**Scenario**: User uploads Excel with merged cells, multiple header rows, or complex formatting

**Flow**:

1. System attempts to process but encounters complexity  
2. Warning message: "Your file contains complex formatting (merged cells, multiple header rows). We've extracted data as best as possible, but some formatting may be lost."  
3. Show preview with how data was interpreted  
4. User can:  
   - Accept interpretation  
   - Upload simplified version  
   - Cancel

### Edge Case 8: Empty Columns or Rows

**Scenario**: Dataset has completely empty columns or rows interspersed

**Flow**:

1. System detects empty columns/rows during preprocessing  
2. Automatically removes empty columns/rows  
3. Summary shows: "Removed 3 empty columns and 15 empty rows"  
4. Final row/column count reflects cleaned data  
5. User can view cleaning log in data settings

---

## 12\. Success Metrics & User Feedback

### Success Criteria

- Upload completion rate: % of started uploads that complete successfully  
- Time to first successful upload: How quickly new users upload first dataset  
- Clarification rate: % of users who clarify AI interpretation  
- Suggestion interaction rate: % of users who click suggested actions  
- Error rate: % of uploads that fail preprocessing

### User Feedback Mechanisms

**Post-Upload Survey** (Optional, shown after 1st upload):

- "How easy was it to upload your data?" (1-5 scale)  
- "Was the AI interpretation accurate?" (Yes/No/Somewhat)  
- "Which suggested action was most helpful?" (Multi-choice)

**Inline Feedback**:

- Thumbs up/down on AI interpretation  
- "Report issue" link if data doesn't look correct

---

## 13\. Future Enhancements (Out of Scope for Initial Release)

### Potential Features

1. **Batch Upload**: Upload multiple files at once  
2. **Data Source Connections**: Connect to databases, APIs, Google Sheets  
3. **Scheduled Refresh**: Auto-update data sources on schedule  
4. **Data Transformation**: Clean, merge, or transform data before saving  
5. **Collaborative Features**: Share data sources with team members  
6. **Version Control**: Track changes to datasets over time  
7. **Advanced AI Training**: Improve AI interpretation with user feedback over time  
8. **Custom Data Models**: Allow users to define custom validation rules  
9. **Data Quality Score**: Show data quality metrics (completeness, consistency)  
10. **Integration with BI Tools**: Export to Tableau, Power BI, etc.

---

## 14\. Technical Considerations

### File Processing Requirements

- **Server-side processing**: All preprocessing happens on backend  
- **Asynchronous handling**: Uploads don't block UI  
- **Scalability**: Support multiple concurrent uploads  
- **Storage**: Secure file storage with encryption  
- **Backup**: Automatic backup of uploaded files

### Data Model Requirements

The platform requires uploaded files to conform to a specific data model. This model defines:

- Required columns (if any)  
- Expected data types (numeric, text, date, boolean)  
- Validation rules (e.g., dates must be in valid format)  
- Structural requirements (tabular format, headers in first row)

**Example Data Model** (for reference):

\- Must have at least 2 columns

\- First row must contain column headers (non-empty strings)

\- At least one column must contain numeric data

\- Date columns must be in recognizable date format (MM/DD/YYYY, YYYY-MM-DD, etc.)

\- No more than 20% of cells in any column can be empty

### AI Integration

- **Context Pipeline**: User context \+ sample data → AI model  
- **Interpretation Generation**: Natural language generation based on data structure  
- **Suggestion Engine**: Pattern matching to suggest relevant actions  
- **Clarification Loop**: Incorporate user feedback to refine understanding

### Security & Privacy

- **Data Encryption**: All uploaded files encrypted at rest and in transit  
- **Access Control**: Data sources only accessible by owning user (or shared users)  
- **Audit Logging**: Track all data access and modifications  
- **Compliance**: GDPR, CCPA compliance for data handling  
- **Data Retention**: Clear policies on how long data is stored

---

## 15\. User Experience Principles

### Design Guidelines

1. **Clarity**: Every step clearly explained, no ambiguity  
2. **Feedback**: Immediate feedback for all actions  
3. **Error Recovery**: Clear paths to recover from errors  
4. **Progressive Disclosure**: Show advanced options only when needed  
5. **Accessibility**: WCAG 2.1 AA compliant (keyboard navigation, screen readers)  
6. **Mobile Responsive**: Optimized for tablets and mobile devices  
7. **Performance**: Fast load times, smooth animations  
8. **Consistency**: Consistent with platform's design system

### Accessibility Requirements

- All form fields have proper labels  
- Error messages associated with form fields  
- Keyboard navigation support throughout flow  
- Screen reader announcements for status changes  
- Color contrast meets WCAG standards  
- Focus indicators clearly visible  
- Alternative text for icons and images

---

# **3. Chat with Data** 

## Document Purpose

This document provides a comprehensive user experience specification for the "Chat with Data" feature—a conversational interface that allows users to analyze and explore their data using natural language queries. It is intended as a definitive guide for UI/UX designers to create detailed interface designs, ensuring consistent implementation across the product.

The following sections detail:

- **Entry Point & Interface Layout** — How users access the feature from the dashboard and the structure of the chat interface
- **Query & Response Flow** — The complete cycle from typing a query to receiving results, including real-time script generation and sandbox execution
- **Data Card System** — Specifications for displaying results (Query Brief, Data Table, Explanation, Visualization) and available actions (Save, PowerPoint Export, Share)
- **Error Handling & Edge Cases** — System responses for processing errors, ambiguous queries, and credit-related scenarios
- **Supporting Elements** — Loading states, session management, accessibility requirements, mobile responsiveness, and animation specifications

---

## 1. Entry Point: Dashboard Screen

### 1.1 Initial State

**Screen:** Main Dashboard

**Elements visible:**
- Navigation sidebar (left)
- Header bar with user profile and notifications
- Main content area displaying available data sources
- Credit balance indicator (top-right corner showing "X credits remaining")

### 1.2 Data Source Selection

**User Action:** User clicks on a data source card (e.g., "Sales Data Q4 2024")

**System Response:**
- Selected data source card highlights with a visual indicator (border glow or checkmark)
- A "Chat with Data" button appears or becomes enabled
- Tooltip displays: "Start analyzing [Data Source Name]"

**Alternative Entry:**
- User can also right-click on data source and select "Chat with Data" from context menu
- Or hover over data source card to reveal quick action buttons

### 1.3 Opening the Chat Interface

**User Action:** User clicks "Chat with Data" button

**System Response:**
- Smooth transition animation (slide-in from right or modal expansion)
- Loading indicator displays: "Preparing your data environment..."
- System loads data schema and metadata in background (2-3 seconds max)

---

## 2. Chat Interface - Main Screen

### 2.1 Interface Layout

**Screen:** Chat with Data Interface

**Layout Structure (recommended: split-panel or full-screen modal):**

```
┌─────────────────────────────────────────────────────────────────┐
│  Header Bar                                                      │
│  [← Back] [Data Source Name] [Credit: XX] [Settings ⚙] [✕ Close]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                          │    │
│  │                    Chat Area                             │    │
│  │              (Conversation History)                      │    │
│  │                                                          │    │
│  │                                                          │    │
│  │                                                          │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 💬 Ask a question about your data...            [Send ➤]│    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [Suggested Prompts: "Show top 10..." | "Compare..." | "Trend.."]│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Header Bar Elements

| Element | Description | Interaction |
|---------|-------------|-------------|
| Back Arrow | Returns to dashboard | Click to exit (with confirmation if conversation exists) |
| Data Source Name | Shows currently selected data source | Click to view data source details/schema |
| Credit Balance | Displays remaining credits | Hover shows tooltip with subscription details |
| Settings Icon | Access chat preferences | Opens settings dropdown |
| Close Button | Closes the chat interface | Click to exit |

### 2.3 Empty State (First Visit)

**Display Elements:**
- Welcome illustration or icon
- Welcome message: "Start exploring your data"
- Brief description: "Ask questions in natural language to analyze, visualize, and understand your data"
- Suggested starter prompts (3-4 clickable chips):
  - "Show me an overview of this data"
  - "What are the top performing categories?"
  - "Show trends over time"
  - "Compare this month vs last month"

### 2.4 Data Schema Panel (Optional - Collapsible)

**Location:** Left sidebar or expandable panel

**Content:**
- List of available tables/datasets
- Column names with data types
- Sample values preview
- Search/filter functionality

**Purpose:** Helps users understand what data is available for querying

---

## 3. Query Submission Flow

### 3.1 Typing a Query

**User Action:** User clicks on input field and types query

**Input Field Behavior:**
- Placeholder text: "Ask a question about your data..."
- Auto-expand for multi-line input (up to 4 lines visible)
- Character counter appears after 200 characters
- Send button activates when text is entered

**Auto-suggestions (Optional Enhancement):**
- As user types, show contextual suggestions based on:
  - Data column names
  - Previous successful queries
  - Common query patterns

### 3.2 Submitting the Query

**User Action:** User clicks Send button or presses Enter

**Immediate System Response:**
1. Input field clears and disables temporarily
2. User's query appears in chat as a message bubble (right-aligned)
3. Credit deduction indicator flashes: "-1 credit"
4. AI response container appears with typing indicator

---

## 4. Response Generation Flow

### 4.1 Processing Indicator

**Display:** AI message bubble with animated typing dots

**Duration indicators:**
- Simple queries: "Analyzing..." (1-3 seconds)
- Complex queries: "Processing your request..." with subtle progress animation

### 4.2 Script Generation Display (When Applicable)

**Trigger:** When the query requires Python script execution

**Visual Presentation:**

```
┌─────────────────────────────────────────────────────────────┐
│ 🔧 Generating analysis script...                            │
├─────────────────────────────────────────────────────────────┤
│ ```python                                                   │
│ # Streaming code appears line by line                       │
│ import pandas as pd                                         │
│                                                             │
│ df = load_data('sales_q4_2024')                            │
│ result = df.groupby('category').sum()...                   │
│ ```                                                         │
│                                                             │
│ [▓▓▓▓▓▓▓▓░░] Generating...                                 │
└─────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Code streams in real-time (typewriter effect)
- Syntax highlighting applied
- Collapsible after completion (default: collapsed)
- "View Script" toggle to show/hide

### 4.3 Script Execution Indicator

**Display:** After script generation completes

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Running analysis...                                      │
│ [▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░] Executing in sandbox                  │
└─────────────────────────────────────────────────────────────┘
```

**States:**
- "Executing in sandbox..."
- "Processing results..."
- "Preparing visualization..." (if applicable)

---

## 5. Data Card Display

### 5.1 Data Card Structure

**Container:** Distinct card component within the chat flow

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Query Result                                    [•••]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ QUERY BRIEF                                                 │
│ ─────────────────────────────────────────────────────────── │
│ Top 10 products by revenue for each category in Q4 2024    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ DATA TABLE                                                  │
│ ─────────────────────────────────────────────────────────── │
│ ┌──────────┬────────────┬───────────┬──────────┐           │
│ │ Rank     │ Product    │ Category  │ Revenue  │           │
│ ├──────────┼────────────┼───────────┼──────────┤           │
│ │ 1        │ Product A  │ Electronics│ $45,230 │           │
│ │ 2        │ Product B  │ Electronics│ $38,100 │           │
│ │ 3        │ Product C  │ Apparel   │ $32,500  │           │
│ │ ...      │ ...        │ ...       │ ...      │           │
│ └──────────┴────────────┴───────────┴──────────┘           │
│                                                             │
│ Showing 10 of 47 results    [Load More] [View Full Table]  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ EXPLANATION                                                 │
│ ─────────────────────────────────────────────────────────── │
│ Electronics dominates the top positions with 6 out of 10   │
│ spots. Product A leads with $45,230 in revenue,            │
│ representing 12% of total category sales.                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ VISUALIZATION                                               │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│     ████████████████████████████  Product A ($45,230)      │
│     ██████████████████████████    Product B ($38,100)      │
│     ████████████████████          Product C ($32,500)      │
│     ██████████████████            Product D ($31,200)      │
│     ████████████████              Product E ($28,900)      │
│                                                             │
│                              [Expand Chart] [Change Type ▼] │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [💾 Save] [📊 To PowerPoint] [📤 Share ▼]                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Data Card Sections Detail

#### Query Brief Section
- **Icon:** 🎯 or similar
- **Content:** AI-generated interpretation of user's query
- **Style:** Slightly emphasized text, 1-2 lines maximum
- **Purpose:** Confirms understanding of user intent

#### Data Table Section
- **Default display:** First 10 rows
- **Features:**
  - Sortable columns (click header to sort)
  - Resizable columns
  - Horizontal scroll for wide tables
  - Row hover highlighting
- **Actions:**
  - "Load More" - loads next 10 rows incrementally
  - "View Full Table" - opens modal with complete dataset

#### Explanation Section
- **Content:** 2-4 sentences summarizing key insights
- **Style:** Regular paragraph text
- **Tone:** Informative, not overly detailed

#### Visualization Section (Conditional)
- **Display condition:** When visual representation adds value
- **Chart types available:**
  - Bar chart (horizontal/vertical)
  - Line chart
  - Pie chart
  - Area chart
  - Scatter plot
- **Interactions:**
  - Hover for tooltips with exact values
  - "Expand Chart" opens fullscreen view
  - "Change Type" dropdown to switch visualization type
  - Download chart as image

### 5.3 Data Card Action Buttons

#### Save Action
**User Action:** Click "Save" button

**System Response:**
1. Modal appears: "Save to Collection"
2. Input field for custom name (pre-filled with query brief)
3. Optional: Select/create collection folder
4. Confirm button

**Success State:**
- Toast notification: "Saved to [Collection Name]"
- Button changes to "Saved ✓" temporarily

#### Generate PowerPoint Action
**User Action:** Click "To PowerPoint" button

**System Response:**
1. Brief loading indicator: "Generating slide..."
2. Preview modal showing slide layout:
   - Title: Query Brief
   - Content: Table (abbreviated if large) + Chart
   - Footer: Data source and timestamp
3. Options:
   - "Download .pptx"
   - "Add to existing presentation" (if applicable)
   - "Customize layout" (advanced)

**Output:** Downloaded .pptx file

#### Share Action
**User Action:** Click "Share" dropdown

**Dropdown Options:**
| Option | Action |
|--------|--------|
| Share via Email | Opens email composer modal with embedded card preview |
| Save as Image | Downloads PNG of the data card |
| Save as PDF | Downloads PDF document with full card content |
| Copy Link | Generates shareable link (if sharing is enabled) |

**Email Sharing Flow:**
1. Modal with recipient email input
2. Optional message field
3. Preview of what will be shared
4. Send button

---

## 6. Conversation Continuation

### 6.1 Follow-up Queries

**Context:** After receiving a Data Card, user can continue the conversation

**Input field re-enables immediately after response completes**

**Contextual Suggestions appear below input:**
- "Drill down into Electronics category"
- "Show this as a trend over time"
- "Compare with Q3 2024"
- "Why is Product A leading?"

### 6.2 Conversation History

**Display:** All messages and Data Cards remain visible in scrollable chat

**Navigation:**
- Smooth scroll through conversation
- "Jump to top" button appears when scrolled down
- Each Data Card is collapsible to reduce clutter

### 6.3 Query Refinement

**Scenario:** User wants to modify previous query

**Options:**
1. Type new query naturally: "Actually, show me top 20 instead"
2. Click "Refine" button on existing Data Card (if implemented)
3. Reference previous results: "From the previous result, filter only Apparel"

---

## 7. Error Handling

### 7.1 Query Processing Errors

**Error Types and Display:**

#### Insufficient Data
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Unable to Complete Query                                 │
├─────────────────────────────────────────────────────────────┤
│ The requested data is not available in this dataset.       │
│                                                             │
│ Available columns: product_name, category, revenue, date   │
│                                                             │
│ Try asking about: revenue trends, category performance,    │
│ product comparisons                                         │
│                                                             │
│ [Suggested: "Show revenue by category"]                    │
└─────────────────────────────────────────────────────────────┘
```

#### Ambiguous Query
```
┌─────────────────────────────────────────────────────────────┐
│ 🤔 Clarification Needed                                     │
├─────────────────────────────────────────────────────────────┤
│ I found multiple interpretations for your query:           │
│                                                             │
│ Did you mean:                                               │
│ ○ Top products by revenue                                  │
│ ○ Top products by units sold                               │
│ ○ Top products by profit margin                            │
│                                                             │
│ [Click an option or type to clarify]                       │
└─────────────────────────────────────────────────────────────┘
```

#### Execution Error
```
┌─────────────────────────────────────────────────────────────┐
│ ❌ Processing Error                                         │
├─────────────────────────────────────────────────────────────┤
│ We encountered an issue while processing your request.     │
│                                                             │
│ [View Technical Details ▼]                                  │
│                                                             │
│ [🔄 Retry] [📝 Rephrase Query] [📞 Contact Support]        │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Credit-Related Scenarios

#### Insufficient Credits
**Trigger:** User attempts query with 0 credits remaining

**Display:**
```
┌─────────────────────────────────────────────────────────────┐
│ 💳 Insufficient Credits                                     │
├─────────────────────────────────────────────────────────────┤
│ You've used all your credits for this month.               │
│                                                             │
│ Credits reset on: [Date]                                   │
│ Or top up now to continue analyzing.                       │
│                                                             │
│ [🛒 Top Up Credits] [📅 View Reset Date]                   │
└─────────────────────────────────────────────────────────────┘
```

#### Low Credit Warning
**Trigger:** Credits fall below threshold (e.g., 5 remaining)

**Display:** Non-intrusive banner above input field
```
⚠️ Low credits: 3 remaining | [Top Up]
```

---

## 8. Additional Interface States

### 8.1 Loading States

| State | Visual | Duration |
|-------|--------|----------|
| Opening chat | Full screen loader with progress | 2-3 seconds |
| Submitting query | Input disabled, send button shows spinner | < 1 second |
| Processing | AI bubble with typing animation | 2-10 seconds |
| Generating script | Streaming code display | 3-15 seconds |
| Executing script | Progress bar in sandbox indicator | 2-20 seconds |
| Rendering results | Data Card skeleton loading | 1-2 seconds |

### 8.2 Empty and Null States

#### No Results Found
```
┌─────────────────────────────────────────────────────────────┐
│ 📭 No Results                                               │
├─────────────────────────────────────────────────────────────┤
│ Your query returned no matching data.                      │
│                                                             │
│ Suggestions:                                                │
│ • Check if the date range includes data                    │
│ • Try broader filter criteria                              │
│ • Verify spelling of category/product names                │
│                                                             │
│ [Show available data ranges]                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Session Management

#### Session Timeout Warning
**Trigger:** 10 minutes of inactivity

**Display:** Toast notification
```
Your session will expire in 5 minutes due to inactivity. [Stay Active]
```

#### Session Expired
**Display:** Modal overlay
```
┌─────────────────────────────────────────────────────────────┐
│ ⏰ Session Expired                                          │
├─────────────────────────────────────────────────────────────┤
│ Your session has timed out for security.                   │
│                                                             │
│ Your conversation history has been saved.                  │
│                                                             │
│ [🔄 Reconnect] [🚪 Return to Dashboard]                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Settings and Preferences

### 9.1 Chat Settings Dropdown

**Access:** Click settings icon in header

**Options:**
| Setting | Description | Default |
|---------|-------------|---------|
| Show generated scripts | Display Python code during processing | On |
| Auto-expand visualizations | Charts expand by default | Off |
| Compact Data Cards | Reduce card padding and spacing | Off |
| Dark mode | Toggle dark/light theme | System |

### 9.2 Data Display Preferences

**Table preferences:**
- Default rows to display: 10 / 25 / 50
- Number formatting: 1,000 vs 1000
- Date format: MM/DD/YYYY vs DD/MM/YYYY

---

## 10. Accessibility Considerations

### 10.1 Keyboard Navigation

| Action | Shortcut |
|--------|----------|
| Focus chat input | `/` or `Ctrl + K` |
| Send message | `Enter` or `Ctrl + Enter` |
| Navigate Data Cards | `Tab` through interactive elements |
| Collapse/Expand sections | `Space` when focused |
| Close modal/dropdown | `Escape` |

### 10.2 Screen Reader Support

- All interactive elements have appropriate ARIA labels
- Data tables include proper header associations
- Charts have text alternatives describing key insights
- Loading states announced to assistive technology

### 10.3 Visual Accessibility

- Minimum contrast ratio of 4.5:1 for text
- Charts use colorblind-friendly palettes
- Focus indicators clearly visible
- Text resizable up to 200% without loss of functionality

---

## 11. Mobile Responsiveness

### 11.1 Layout Adaptations

**Breakpoints:**
- Desktop: > 1024px (full layout as described)
- Tablet: 768px - 1024px (collapsible sidebar)
- Mobile: < 768px (stacked layout, bottom sheet for cards)

### 11.2 Mobile-Specific Interactions

- Data Cards open as bottom sheets
- Tables horizontally scrollable with swipe
- Charts tappable for detail view
- Voice input option for queries

---

## 12. Flow Summary Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Dashboard   │────▶│ Select Data  │────▶│ Open Chat    │
│              │     │   Source     │     │  Interface   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────┐
│                    CHAT INTERFACE                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                                                      │ │
│  │  ┌─────────────┐    ┌─────────────┐                 │ │
│  │  │ User types  │───▶│  -1 Credit  │                 │ │
│  │  │   query     │    │  deducted   │                 │ │
│  │  └─────────────┘    └──────┬──────┘                 │ │
│  │                            │                         │ │
│  │                            ▼                         │ │
│  │              ┌─────────────────────────┐             │ │
│  │              │   Processing Query      │             │ │
│  │              │  ┌─────────────────┐    │             │ │
│  │              │  │ Generate Script │    │             │ │
│  │              │  │   (if needed)   │    │             │ │
│  │              │  └────────┬────────┘    │             │ │
│  │              │           ▼             │             │ │
│  │              │  ┌─────────────────┐    │             │ │
│  │              │  │Execute in       │    │             │ │
│  │              │  │Sandbox          │    │             │ │
│  │              │  └────────┬────────┘    │             │ │
│  │              └───────────┼─────────────┘             │ │
│  │                          ▼                           │ │
│  │              ┌─────────────────────────┐             │ │
│  │              │     DATA CARD           │             │ │
│  │              │  • Query Brief          │             │ │
│  │              │  • Data Table           │             │ │
│  │              │  • Explanation          │             │ │
│  │              │  • Visualization        │             │ │
│  │              │  ─────────────────────  │             │ │
│  │              │  [Save][PPT][Share]     │             │ │
│  │              └───────────┬─────────────┘             │ │
│  │                          │                           │ │
│  │                          ▼                           │ │
│  │              ┌─────────────────────────┐             │ │
│  │              │ Continue Conversation?  │◀────┐       │ │
│  │              │    [Yes]     [Exit]     │     │       │ │
│  │              └─────┬───────────────────┘     │       │ │
│  │                    │                         │       │ │
│  │                    └─────────────────────────┘       │ │
│  │                                                      │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## Appendix A: Component Specifications

### A.1 Data Card Component Props

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| queryBrief | string | Yes | AI interpretation of query |
| tableData | array | Yes | Array of row objects |
| tableColumns | array | Yes | Column definitions |
| explanation | string | No | Summary text |
| visualization | object | No | Chart configuration |
| timestamp | datetime | Yes | Query execution time |
| queryId | string | Yes | Unique identifier |

### A.2 Credit Display Component

| State | Display | Color |
|-------|---------|-------|
| Sufficient (>10) | "XX credits" | Green |
| Low (5-10) | "XX credits" + warning icon | Yellow |
| Critical (1-4) | "XX credits" + alert | Orange |
| Empty (0) | "No credits" | Red |

---

## Appendix B: Animation Specifications

| Interaction | Animation Type | Duration | Easing |
|-------------|---------------|----------|--------|
| Chat open | Slide in from right | 300ms | ease-out |
| Message appear | Fade + slide up | 200ms | ease-out |
| Data Card expand | Height expansion | 250ms | ease-in-out |
| Button hover | Scale + shadow | 150ms | ease |
| Loading dots | Opacity pulse | 1000ms | linear (loop) |
| Code streaming | Typewriter | 20ms/char | linear |

# **4. Collections & Settings**

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
