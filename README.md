[![Python 2.6 2.7 3.7](https://img.shields.io/badge/python-2.6%20%7C%202.7%20%7C%203.7-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

# Nuke Version Dropper

This ShotGrid will add the ability to drop versions from within the ShotGrid webbrowser into Nuke.
Useful for a stock library! :)

It will add a callback on every Nuke session to listen for URL's being dropped into Nuke. When it is dropped, it will look up the corresponding item to load as a read node.

The credentials to search for the item will be the one from the session itself. So no need to add any API credentials.

![Dragging and dropping](https://raw.githubusercontent.com/nfa-vfxim/tk-nuke-versiondropper/master/resources/tk-nuke-versiondropper.gif)

## How to install
### Add tk-nuke-versiondropper to `app_locations.yml`
Add the following lines to `app_locations.yml` in your config ([example](https://github.com/nfa-vfxim/nfa-shotgun-configuration/blob/003162907668fce1ab575a3a0738ff8ca608c5b3/env/includes/app_locations.yml#L257 "Example in the Filmacademy ShotGrid config")):
```buildoutcfg
apps.tk-nuke-versiondropper.location:
  type: github_release
  organization: nfa-vfxim
  repository: tk-nuke-versiondropper
  version: 0.1.3
```

### 2. Add tk-nuke-versiondropper to `tk-nuke.yml`
Add the following lines to `tk-nuke.yml` in your config ([example](https://github.com/nfa-vfxim/nfa-shotgun-configuration/blob/a172e698de5ea54cfd6a8743d9d501b69039885d/env/includes/settings/tk-nuke.yml#L132 "Example in the Filmacademy ShotGrid config"))
```buildoutcfg
settings.tk-nuke.project:
  apps:
    tk-nuke-versiondropper:
      location: "@apps.tk-nuke-versiondropper.location"
```
### 3. That's it :)
