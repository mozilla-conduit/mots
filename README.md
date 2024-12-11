mots - Module Ownership in Tree System
======================================

[Full documentation](https://mots.readthedocs.io/en/latest/) can be viewed online.

### Contributing

- All contributors must abide by the Mozilla Code of Conduct.

- The [main repository](https://github.com/mozilla-conduit/mots) is hosted on GitHub. Pull requests should be submitted against the `main` branch.

- Bugs are tracked [on Bugzilla](https://bugzilla.mozilla.org), under the `Conduit :: mots` component.


Development environment
=======================
To set up a local development environment, run the following commands. Optionally replace the python version with the desired version on your local machine.


```shell
make dev-env PY=python3.9
make dev
```

The above commands will set up a virtual environment using the provided Python version available on your machine, and subsequently install all required packages in that environment, which can be found in the `.mots-env` directory.

Impact on other applications
============================
When making a significant or breaking change to mots, the pinned version of mots should be updated in the following:
- [mach doc](https://searchfox.org/mozilla-central/source/python/sites/docs.txt)
- [Lando](https://github.com/mozilla-conduit/lando-api/blob/main/requirements.in) (legacy)
- [Lando](https://github.com/mozilla-conduit/lando/blob/main/requirements.txt)
