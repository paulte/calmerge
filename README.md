# calmerge

`calmerge` downloads multiple iCalendar (ICS) feeds, merges them into a single calendar, and writes the result as a new ICS file.

The project is designed around a simple idea:

- **This repository** contains the reusable application.
- **Your repository** contains your private configuration, generated calendars and deployment automation.

This keeps calendar URLs and personal data out of the public codebase.

---

# Installation

Create a virtual environment and install directly from GitHub:

```shell
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install git+https://github.com/paulte/calmerge.git
```

For development:

```shell
git clone https://github.com/paulte/calmerge.git
cd calmerge

python3 -m venv venv
. venv/bin/activate

pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .

pre-commit install
```

Optional development tooling:

```shell
brew install actionlint
```

---

# Configuration

By default, `calmerge` reads its configuration from:

```text
calendars.yaml
```

You can specify a different file:

```shell
calmerge --config my-calendars.yaml
```

An example configuration is included in:

```text
examples/calendars.example.yaml
```

## Example

```yaml
---
calendar_name: Merged Family Calendar

calendars:
  - name: Work
    prefix: Work
    url: https://example.com/work.ics

  - name: Family
    prefix: Family
    url: https://example.com/family.ics

  - name: Scouts
    prefix: Scouts
    url: https://example.com/scouts.ics
```

## Calendar options

Each calendar requires:

| Option | Description |
|---------|-------------|
| `name` | Friendly name of the calendar |
| `url` | ICS feed URL |

Optional settings include:

| Option | Description |
|---------|-------------|
| `prefix` | Prepended to event titles to identify their source |

Additional filtering and processing options may also be configured as the project evolves.

---

# Running

Generate the merged calendar:

```shell
calmerge
```

Or specify a configuration file:

```shell
calmerge --config calendars.yaml
```

The merged calendar is written to:

```text
calendars/merged.ics
```

Downloads are cached automatically to minimise unnecessary network traffic.

---

# Recommended repository layout

A typical deployment keeps the public application separate from private data.

## Public repository

```
calmerge/
├── src/
├── tests/
├── examples/
├── README.md
└── ...
```

## Private repository

```
.
├── calendars.yaml
├── calendars/merged.ics
└── .github/workflows/
```

Your private repository contains everything specific to your calendars, while the application itself can simply be installed from GitHub.

---

# Development

Format code:

```shell
make format
```

Run linting:

```shell
make lint
```

Run the full validation suite:

```shell
make check
```

Remove generated files:

```shell
make distclean
```

---

# Automation

`calmerge` is intended to run unattended from your private github repo

A typical GitHub Actions workflow:

1. Checks out your private repository.
2. Installs `calmerge` from GitHub.
3. Runs `calmerge`.
4. Commits updated calendars if anything changed.
5. Publishes the generated calendar.

Because configuration, cache and output all live in your private repository, updating to new versions of `calmerge` is handled automatically within the github action within the private repo.

---

# Deployment

The generated `merged.ics` file can be published using any static hosting provider, including:

- GitHub Pages
- Cloudflare Pages
- Netlify
- Any standard web server

The published ICS URL can then be subscribed to from calendar applications such as Apple Calendar, Google Calendar and Outlook.

---

# Project philosophy

`calmerge` deliberately separates **code** from **configuration**.

This repository contains only the reusable application.

Your private repository contains:

- calendar URLs
- configuration
- merged generated calendar
- deployment workflow

This makes it easy to:

- keep personal data private
- upgrade to new releases
- reuse the application across multiple deployments
- contribute improvements back to the public project
