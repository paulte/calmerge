# calmerge

`calmerge` downloads multiple iCalendar (ICS) feeds, merges them into a single calendar, and writes the result as a new ICS file.

The project is structured as follows:

- **This repository** https://github.com/paulte/calmerge/ contains the reusable application.  You will not need to reference or clone this repo
- **Your repository**  cloned from https://github.com/paulte/calmerge.exampleprivaterepo.  Your repo contains your private configuration and will reference the above calmerge code via GitHub actions.

This keeps calendar URLs and personal data out of the public codebase.

---

# Installation

This setup assumes you have already setup ssh key based auth for your github account.

* Create a private repo within your github account.  For example, ```calmerge.config```
* Set visibility Private and do not initialise the repo with any files.
* You will end up with a repo name such as ```git@github.com:yourgithubaccount/calmerge.config.git```

Set your ```GITHUBACCOUNT``` variable, clone the example config and then push back to your private repo:

```bash
export GITHUBACCOUNT="yourgithubaccount"
git clone https://github.com/paulte/calmerge.exampleprivaterepo.git calmerge.config
cd calmerge.config
git remote set-url origin git@github.com:${GITHUBACCOUNT}/calmerge.config
git push
```

Copy the example calendar to the main configuration, update to include the ics files you wish to merge and then push back 
Move ```calendars.example.yaml``` to ```calendars.yaml```, adjust to adding all required calendars and commit

```bash
cp calendars.example.yaml calendars.yaml
<edit calendars.yaml>
git add calendars.yaml
pre-commit init
make check
git commit -m"initial configuration"
git push

Note, when doing the ```git commit```, pre-commit will validate the config file before allowing a remote push

Once the changes have been pushed, a GitHub action will automatically trigger to download, merge and create a ```calendars/merged.ics``` file within your repo.  Navigate to your calmerge.config repository on GitHub, click on Actions and you should see a recently executed green workflow.

Once your config repository is working, choose a mechanism to publicly present the calendar under an obfuscated name.

A cloud flare example follows:
- create a free cloud flare account and login
- under works and pages, select Create application
- Click on "Looking to deploy pages?   Get Started"
- Import an existing Git repository
- Authenticate and select your GitHub account and repository
- select your calmerge.config repository
- Enter the following under Build command, replacing with your own random GUID:
```bash
mkdir -p public/ac1f7e02-b0df-4596-9ebb-259c8c775412 && cp calendars/merged.ics public/ac1f7e02-b0df-4596-9ebb-259c8c775412/events.ics
- Once the build has complete, there will be a "You can preview your project at...  Click on this link and append the ```public/ac1f7e02-b0df-4596-9ebb-259c8c775412/events.ics``` path.  
- your browser should download the merged ics file.
- Copy this URL and subscribe in your calendar apps, for example ```https://calmerge-config.pages.dev/public/ac1f7e02-b0df-4596-9ebb-259c8c775412/events.ics`

At this point, your configuration is complete.  As one last check, perform a dummy change such as changing the prefix for a calendar.
- Check GitHub actions - you should notice a recently executed workflow running to green and notice an updated  ```calendars/merged.ics``` file in the repo
- Check Cloudflare.  You should notice the git commit being absorbed and the merged.ics calendar being published

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
