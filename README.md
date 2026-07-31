# calmerge

This repo contains the code for `calmerge`, a tool that downloads multiple ICS calendars and merges them into a single calendar.

The application code is designed to be public. Calendar configuration and generated state can be maintained separately in a private repository.

## Environment setup

### Production

```shell
git clone https://github.com/paulte/calmerge.git
cd calmerge
python3 -m venv venv
. venv/bin/activate
python3 -m pip install --upgrade pip
pip install .
```

### Development

```shell
pip install -r requirements-dev.txt
pip install -e .
pre-commit install
```

Install development tools:

```shell
brew install actionlint
```

## Configuration

Calendar sources are configured in a YAML file. By default this is `calendars.yaml`, but an alternative file can be supplied using `--config`.

The public repository contains an example configuration:

```shell
examples/calendars.example.yaml
```

Private deployments should maintain their own configuration file separately.
### Example

```yaml
---
calendar_name: My Combined Calendar

calendars:
  - name: Work Calendar
    url: https://example.com/work-calendar.ics

  - name: Family Calendar
    prefix: Family
    url: https://example.com/family-calendar.ics

  - name: Events Calendar
    prefix: Events
    url: https://example.com/events-calendar.ics
```

The minimum configuration for each calendar source is:

- `name` - the display name of the source calendar
- `url` - the ICS calendar URL

Optional settings can be used to customise processing, such as:

- `prefix` - optional text added to event titles to identify the source calendar

The configuration file is intentionally kept separate from the codebase. This allows the calmerge package to be public while keeping personal calendar sources private.

## Repository separation

The application code and calendar instance data are intentionally separated.

The public repository contains:

- application code
- tests
- CI workflows
- example configuration
- documentation

A private configuration repository contains deployment-specific data:

- `calendars.yaml`
- calendar source URLs
- generated calendar output
- cached calendar state

This allows the `calmerge` application to be reused without exposing private calendar sources or personal calendar data.

## Usage

Generate the merged calendar:

```shell
calmerge
```

The generated calendar will be written to `calendars/merged.ics`.

## Development commands

Format code:

```shell
make format
```

Run Lint checks
```shell
make lint
```

Run the full validation suite:
```shell
make check
```

Clean generated files:
```shell
make distclean
```

## Deployment and automation

The `calmerge` package is designed to separate calendar processing code from calendar configuration and generated output.

The public repository contains the reusable `calmerge` code. A separate private repository can contain:

- calendar source configuration
- private calendar URLs
- generated calendar output
- deployment automation

This allows the `calmerge` package to be shared without exposing personal calendar sources.

### GitHub Actions

A private configuration repository can use GitHub Actions to periodically run `calmerge`.

A typical workflow:

1. Checks out the private configuration repository.
2. Installs the `calmerge` package from GitHub.
3. Loads the private `calendars.yaml` configuration.
4. Downloads and merges the configured ICS calendars.
5. Commits the generated calendar output if it has changed.

The refresh frequency is controlled by the workflow schedule configuration.

### Publishing

The generated calendar can then be published using a static hosting provider such as Cloudflare Pages or another web hosting service.

### Deployment flow

```text
Source calendars
        |
        v
GitHub Actions
        |
        v
Calendar merge process
        |
        v
calendars/merged.ics
        |
        v
Git commit
        |
        v
Cloudflare deployment
        |
        v
Published calendar URL
```
