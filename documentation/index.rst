.. toctree::
   :maxdepth: 2
   :caption: Contents:


Developer Interface
===================

Module
------
.. automodule:: mots.module
    :members:


Directory
---------
.. automodule:: mots.directory
    :members:


CLI
---------
.. automodule:: mots.cli
    :members:


Config
---------
.. automodule:: mots.config
    :members:


Utils
---------
.. automodule:: mots.utils
    :members:

Command Line Usage
==================
You can get this help by typing ``mots`` at the command line.

usage: mots [-h] [--debug] {init,module,validate,clean,query} ...

main command line interface for mots

optional arguments:
  -h, --help            show this help message and exit
  --debug               enable debug output

commands:
  {init,module,validate,clean,query}
    init                initialize mots configuration in repo
    module              module_operations
    validate            validate mots config for current repo
    clean               clean mots config for current repo
    query               query the module directory

usage: mots init [-h] [--path PATH]

optional arguments:
  -h, --help            show this help message and exit
  --path PATH, -p PATH  the path of the repo to initialize

usage: mots module [-h] [--path PATH] {list,add,show} ...

optional arguments:
  -h, --help            show this help message and exit
  --path PATH, -p PATH  the path of the repo config file

module:
  {list,add,show}
    list                list all modules
    add                 add a new module
    show                show a module

usage: mots validate [-h] [--path PATH] [--repo-path REPO_PATH]

optional arguments:
  -h, --help            show this help message and exit
  --path PATH, -p PATH  the path of the repo config file
  --repo-path REPO_PATH, -r REPO_PATH
                        the path of the repo

usage: mots clean [-h] [--path PATH] [--repo-path REPO_PATH]

optional arguments:
  -h, --help            show this help message and exit
  --path PATH, -p PATH  the path of the repo config file
  --repo-path REPO_PATH, -r REPO_PATH
                        the path of the repo

usage: mots query [-h] [--path PATH] paths [paths ...]

positional arguments:
  paths                 a list of paths to query

optional arguments:
  -h, --help            show this help message and exit
  --path PATH, -p PATH  the path of the repo config file

Development environment
=======================
To set up a local development environment, run the following commands. Replace the python version with the desired version on your local machine.

.. code-block:: bash

    make dev-env PY=python3.9
    source .mots-env/bin/activate
    make dev

The above commands will set up a local development environment using the provided python version available on your machine, and subsequently install all required packages in that environment.

Generate coverage report
------------------------

To generate a standard coverage report, run:

.. code-block:: bash

	make cov

To generate an html coverage report, run:

.. code-block:: bash

	make cov-html
	make serve-cov

Then navigate to your web browser.

Other make commands
-------------------
Run `make` to see all available commands.

.. code-block:: bash

	usage: make <target>

	target is one of:
		help          show this message and exit
		build         build the python package and wheels
		clean         remove temporary files
		cov           run coverage check
		cov-html      generate html coverage report
		dev           setup local dev environment by installing required packages, etc.
		dev-env       create a python virtual environment in ./mots-env
		docs          generate documentation
		requirements  regenerate requirements.txt
		serve-cov     simple http server for coverage report
		serve-docs    simple http server for docs
