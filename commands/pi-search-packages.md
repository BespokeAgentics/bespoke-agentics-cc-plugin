---
name: bespokeagentics:pi-search-packages
description: Search Pi packages and recommend the best fits
argument-hint: <query> [--limit N]
allowed-tools: Skill(pi-assistant)
---

Use the pi-assistant skill to search Pi packages for: $ARGUMENTS

Run `python3 skills/pi-assistant/scripts/search_pi_packages.py` before browsing manually. Summarize the best matches, why they fit, and the exact `pi install` commands the user would use.
