---
created: 2026-02-04T19:06
title: Render markdown in DataCard analysis section
area: ui
files:
  - frontend/src/components/chat/DataCard.tsx
  - frontend/src/components/chat/ChatMessage.tsx
---

## Problem

The DataCard component displays the AI analysis text as raw markdown instead of rendering it with proper formatting. Currently shows markdown syntax like `##`, `**bold**`, `- list items` as plain text.

The onboarding dialog (FileUploadZone and FileInfoModal) already renders markdown correctly using react-markdown with remark-gfm and @tailwindcss/typography prose classes. DataCard should match this formatting for consistency and readability.

Users see unformatted markdown in chat analysis results, making it harder to read compared to the nicely formatted analysis in the upload dialog.

## Solution

Apply the same markdown rendering approach used in FileUploadZone/FileInfoModal:

1. Import react-markdown and remark-gfm in DataCard.tsx
2. Wrap the explanation/analysis text with ReactMarkdown component
3. Add prose classes: `prose prose-sm dark:prose-invert max-w-none`
4. Pass remarkPlugins={[remarkGfm]} for GitHub-flavored markdown support

Example from FileInfoModal that works:
```tsx
<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  className="prose prose-sm dark:prose-invert max-w-none"
>
  {analysis}
</ReactMarkdown>
```

This will format headings, bold text, lists, and tables properly in the DataCard analysis section, matching the polished look of the onboarding dialog.
