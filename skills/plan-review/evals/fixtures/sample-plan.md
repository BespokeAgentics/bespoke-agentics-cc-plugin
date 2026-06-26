# Plan: Add user "preferences" with a dark-mode toggle

## Goal

Let users set preferences. Start with a dark-mode toggle on the settings page. Should work well and
feel fast.

## Background

All API authentication is handled in `src/middleware/auth.ts`, so any new preferences endpoint is
automatically protected — nothing extra to do there. We don't store any per-user settings today.

## Steps

1. Add a `theme` column to the `users` table (values: `light`, `dark`).
2. Add a `PATCH /api/users/me/preferences` endpoint that updates the theme.
3. Add a dark-mode toggle to `src/components/SettingsPage.tsx`.
4. Read the theme on app load and apply it.
5. Also add notification preferences, a language picker, and a "delete my account" button while we're
   in the settings page.
6. Make the toggle look nice.

## Acceptance

- The toggle works.
- It should be fast.

## Notes

We'll ship it straight to production once it's done.
