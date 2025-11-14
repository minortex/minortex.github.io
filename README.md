# Minortex's Blog

This repository contains the source for Minortex's personal blog, built with [Hugo](https://gohugo.io/).

## Commit Guidelines

To maintain a clean and readable git history, please follow these simplified commit conventions. All commit messages must be in English.

### 1. New Article

When adding a new article, use the `new` type.

**Format:**
`new: add new article about <topic>`

**Example:**
`new: add new article about linux swap`

### 2. Modifying an Article

When modifying an existing article, use `docs` for content updates or `fix` for correcting mistakes (e.g., typos).

**The commit scope `()` is required and must contain the article's folder name.** The folder name is the one found under `content/posts/`.

**Format:**
`<type>(<article-folder-name>): <description of change>`

**Examples:**

- To update the content of the article in the `about_swap_on_linux` folder:
  `docs(about_swap_on_linux): clarify the section on zswap`

- To fix a typo in the article in the `credit_card` folder:
  `fix(credit_card): correct typo in the introduction`

### 3. Blog Features and Infrastructure

When adding new features or making changes to the blog's infrastructure (configuration, theme, build system, etc.), use the `site` type.

**Format:**
`site: <description of feature or infrastructure change>`

**Examples:**

- Add new functionality:
  `site: add RSS feed support`

- Update theme or styling:
  `site: update color scheme in theme config`

- Upgrade dependencies:
  `site: upgrade Hugo to version 0.120.0`

- Improve blog siteures:
  `site: enable minification for CSS and JS`

### 4. Chores

Maintenance tasks that don't modify the blog content or functionality, such as updating dependencies, renaming directories, or other housekeeping activities.

**Format:**
`chore: <description of maintenance task>`

**Examples:**

- Rename directories:
  `chore: rename the post directory`

- Update theme submodule:
  `chore: update blowfish theme to latest version`

- Clean up repository:
  `chore: remove unused assets`

- Update gitignore:
  `chore: add build artifacts to .gitignore`
