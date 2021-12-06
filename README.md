[![Python 2.6 2.7 3.7](https://img.shields.io/badge/python-2.6%20%7C%202.7%20%7C%203.7-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting](https://img.shields.io/badge/PEP8%20by-Hound%20CI-a873d1.svg)](https://houndci.com)

# Nuke Version Dropper

This ShotGrid will add the ability to drop versions from within the ShotGrid webbrowser into Nuke.
Useful for a stock library! :)

It will add a callback on every Nuke session to listen for URL's being dropped into Nuke. When it is dropped, it will look up the corresponding item to load as a read node.

The credentials to search for the item will be the one from the session itself. So no need to add any API credentials.

![Dragging and dropping](https://raw.githubusercontent.com/nfa-vfxim/tk-nuke-versiondropper/master/resources/tk-nuke-versiondropper.gif)

## How to install
### Add tk-nuke-versiondropper to `app_locations.yml`
Add the following lines to `app_locations.yml` in your config:
```buildoutcfg
apps.tk-nuke-versiondropper.location:
  type: github_release
  organization: nfa-vfxim
  repository: tk-nuke-versiondropper
  version: 0.1.1
```

### 2. That's it :)
