# Pi Packages Reference

## Contents

- Install and manage packages
- Package sources
- Package structure
- Package authoring notes
- Scope and deduplication

## Install and Manage Packages

Common package commands:

```bash
pi install npm:@scope/pkg@1.2.3
pi install git:github.com/user/repo@v1
pi install https://github.com/user/repo
pi install /absolute/path/to/package
pi install ./relative/path/to/package

pi remove npm:@scope/pkg
pi list
pi update
```

By default, `install` and `remove` write to global settings:

- `~/.pi/agent/settings.json`

Use `-l` to write to project settings instead:

- `.pi/settings.json`

Project settings can be committed and shared; Pi installs missing packages automatically on startup.

## Package Sources

Supported package source families:

- npm: `npm:@scope/pkg@1.2.3`
- git shorthand: `git:github.com/user/repo@v1`
- URL: `https://github.com/user/repo@v1`
- local path: `/absolute/path` or `./relative/path`

Notes:

- project npm installs live under `.pi/npm/`
- git installs are cloned into Pi-managed directories
- local paths are referenced directly and not copied
- `pi -e ...` installs an extension package temporarily for the current run

## Package Structure

Pi packages can declare resources in `package.json`:

```json
{
  "name": "my-package",
  "keywords": ["pi-package"],
  "pi": {
    "extensions": ["./extensions"],
    "skills": ["./skills"],
    "prompts": ["./prompts"],
    "themes": ["./themes"]
  }
}
```

If no `pi` manifest is present, Pi auto-discovers conventional directories:

- `extensions/`
- `skills/`
- `prompts/`
- `themes/`

Use the `pi-package` keyword for discoverability in the gallery.

## Package Authoring Notes

- Put ordinary runtime dependencies in `dependencies`.
- If the package imports Pi core packages such as `@mariozechner/pi-coding-agent`, use `peerDependencies` with `"*"` ranges.
- Prefer conventional directories unless the package truly needs custom path filtering.
- Add README-level install examples that show both global and project-local `pi install` usage.

## Scope and Deduplication

The same package can appear in both global and project settings. If it does, the project entry wins.

Identity rules:

- npm: package name
- git: repository URL without the ref
- local: resolved absolute path

When recommending installs:

- use project-local installs for team workflows or repo-specific behavior
- use global installs for personal utilities and cross-project defaults
