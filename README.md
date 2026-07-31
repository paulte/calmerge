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
pip i nstall .
```

### Development

Requirements:

- Python 3.13+
- pytest
- ruff
- yamllint
- actionlint

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
calendar_name: Scouting Calendar

calendars:
  - name: 1st Malden Scouts
    prefix: Scouts
    url: https://example.com/scouts.ics

  - name: Lucy DofE Bronze Programme
    prefix: LucyDofE
    url: https://example.com/dofe.ics
```


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

The calendar generation process can be automated using GitHub Actions.

A deployment uses the public `calmerge` code repository together with a private configuration repository. GitHub Actions checks out both repositories, installs the `calmerge` package, loads the private configuration, and generates the merged calendar.


### GitHub Actions

GitHub Actions regularly refreshes the source calendars and generates the merged calendar. The workflow runs on a schedule, downloads the configured source calendars, merges the events into `calendars/merged.ics`, checks whether the generated calendar has meaningful changes, and commits updated calendar files back to the repository only when required. The workflow can also be run manually from the GitHub Actions interface.

Calendar refresh frequency is controlled by the workflow schedule configuration.

### Cloudflare publishing

Cloudflare publishes the generated calendar as a static file. When changes are committed to the repository, Cloudflare detects the updated repository state, triggers a new deployment, and publishes `calendars/merged.ics`. Calendar applications can then subscribe to the published URL.

This separates calendar generation from publishing:

- GitHub Actions handles fetching, processing, and validating calendar data.
- Cloudflare handles hosting and serving the final calendar file.

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
