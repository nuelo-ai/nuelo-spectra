---
created: 2026-02-08T20:30:00Z
title: Show suggestions in Data Summary sidebar panel
area: ui
files:
  - frontend/src/components (Data Summary panel)
---

## Problem

Query suggestions are only visible on the empty chat state. Once a user starts chatting, the suggestions disappear and there's no way to rediscover them. If user clicks the (i) info icon on a file in the left sidebar to view the Data Summary, the stored suggestions could be surfaced there as clickable chips — giving users a persistent way to access suggested queries even mid-conversation.

## Solution

In the Data Summary panel (shown when clicking the info icon on a file in the sidebar), display the stored suggestion chips at the top of the data analysis summary. Clicking a chip from the Data Summary panel should populate the chat input (or auto-send based on YAML config) for that file's chat tab. Suggestions are already stored in DB from onboarding, so no additional generation needed — just a UI integration.
