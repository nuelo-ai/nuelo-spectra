# Login Flow - Product Requirement Document

## 1. Sign Up Using Email

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
   - System displays confirmation message: "Account created! Please check your email to verify your account"
9. User receives verification email with a unique link
10. User clicks verification link
11. System verifies the token and marks account as "verified"
12. System redirects user to login page or automatically logs user in
13. System displays success message: "Email verified successfully!"

### Edge Cases
- User tries to sign up with an already registered email → Display: "This email is already registered. Please log in or use a different email"
- Verification email not received → Provide "Resend verification email" option
- Verification link expires (e.g., after 24 hours) → Display error and offer to resend verification email

---

## 2. Sign Up Using Google Account

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

## 3. Login Using Email

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

## 4. Login Using Google Account

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

## 5. Forgot Password

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
