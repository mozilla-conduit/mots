======================================
mots - Module Ownership in Tree System
======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Installation
============
mots can be installed using pip:

.. code-block:: shell

    $ pip install mots


To install the latest version, make sure to pass the ``--upgrade`` flag:

.. code-block:: shell

    $ pip install mots --upgrade


You can check for pre-releases by passing ``--pre`` to the ``pip install`` command:

.. code-block:: shell

    $ pip install mots --pre --upgrade

Installing pre-releases gives you early access to features or bug fixes, and helps with testing.


Command Line Usage
==================
You can get command line usage help by typing ``mots --help`` at the command line.

Initializing a repo
~~~~~~~~~~~~~~~~~~~
To create an initial ``mots.yaml`` file in the current repo, run the following command:

.. code-block:: shell

    $ mots init

This will create an empty configuration file that looks like this:

.. code-block:: yaml

    repo: test-repo
    created_at: '2022-02-11T12:38:57.241494'
    updated_at: '2022-02-11T12:38:57.241550'
    people: []
    modules: []


Adding a Module
~~~~~~~~~~~~~~~
To add a new module to your mots configuration, you can either add it directly to the YAML file, or you could use the interactive ``mots module add`` command.

.. code-block:: shell

    $ mots module add
    Enter a machine name for the new module (e.g. core_accessibility): example
    Enter a human readable name (e.g. Core: Accessibility): Example
    Enter a description for the new module: This is an example module.
    Enter a comma separated list of owner bugzilla IDs: 633708
    Enter a comma separated list of peer bugzilla IDs:
    Enter a comma separated list of paths to include: example.text
    Enter a comma separated list of paths to exclude:
    Enter a machine name of the parent module (optional):

The above code will create a new module in ``mots.yaml`` so that the file will look like this:

.. code-block:: yaml

    repo: test-repo
    created_at: '2022-02-14T09:08:38.055168'
    updated_at: '2022-02-14T09:10:08.096987'
    people: []
    modules:
      - machine_name: example
        name: Example
        description: This is an example module.
        includes:
          - example.text
        excludes: []
        owners:
          - bmo_id: 633708
        peers: []
        meta:


Note that the only required attribute under "owners" is the ``bmo_id`` field. You can optionally add this information manually, and then run the ``mots clean`` command which will query the Bugzilla API to fetch the remaining information.


.. code-block:: yaml

    repo: test-repo
    created_at: '2022-02-14T09:08:38.055168'
    updated_at: '2022-02-14T09:11:32.991309'
    people:
      - &zeid
        bmo_id: 633708
        name: Zeid Zabaneh
        info: '[:zeid]'
        nick: zeid
    modules:
      - machine_name: example
        name: Example
        description: This is an example module.
        includes:
          - example.text
        excludes: []
        owners:
          - *zeid
        peers: []
        meta:


Adding a Submodule
~~~~~~~~~~~~~~~~~~
To add a submodule, follow the same instructions for adding a module, but specify the machine name of the parent module at the input prompt. For example:

.. code-block:: shell

	$ mots module add
	Enter a machine name for the new module (e.g. core_accessibility): example_submodule
	Enter a human readable name (e.g. Core: Accessibility): Example Submodule
	Enter a description for the new module: This module is a submodule of the "Example" module.
	Enter a comma separated list of owner bugzilla IDs:
	Enter a comma separated list of peer bugzilla IDs: 633708
	Enter a comma separated list of paths to include: example_submodule/**/*
	Enter a comma separated list of paths to exclude:
	Enter a machine name of the parent module (optional): example
	$ mots clean

This will result in a file that looks like this:

.. code-block:: yaml

    repo: test-repo
    created_at: '2022-02-14T09:08:38.055168'
    updated_at: '2022-02-14T09:32:52.387222'
    people:
      - &zeid
        bmo_id: 633708
        name: Zeid Zabaneh
        info: '[:zeid]'
        nick: zeid
    modules:
      - machine_name: example
        name: Example
        description: This is an example module.
        includes:
          - example.text
        excludes: []
        owners:
          - *zeid
        peers: []
        meta:
        submodules:
          - machine_name: example_submodule
            name: Example Submodule
            description: This module is a submodule of the "Example" module.
            includes:
              - example_submodule/**/*
            excludes: []
            owners: []
            peers:
              - *zeid
            meta:


Adding a new person
~~~~~~~~~~~~~~~~~~~

Currently, adding a new person to the list of people in ``mots.yaml`` is a manual process. Follow these steps to add a new person:

- Make sure the person does not exist under ``people``
- Add a new entry to ``people`` and provide the ``bmo_id`` under that entry
- run ``mots clean``

There is currently a known issue where the first pass of ``mots clean`` will fail if the other keys are missing from the new entry. If you run into a ``KeyError``, just run ``mots clean`` again. This issue is being tracked in `bug 1797083 <https://bugzilla.mozilla.org/show_bug.cgi?id=1797083>`_.


Cleaning ``mots.yaml``
~~~~~~~~~~~~~~~~~~~~~~

Use ``mots clean`` to automatically sort and synchronize data in the ``mots.yaml`` configuration file. This command requires a ``MOTS_BUGZILLA_API_KEY`` environment variable to be set, or the key to be defined in your settings. You can do this by running the following commands, replacing the redacted key with an actual Bugzilla API key:

.. code-block:: shell

    $ mots settings write BUGZILLA_API_KEY
    $ Enter value for BUGZILLA_API_KEY: <hidden input>
    2022-10-20 15:02:40,439 cli        INFO     BUGZILLA_API_KEY is now set to ********** (str) in overrides file.
    2022-10-20 15:02:40,442 cli        INFO     Success!
    $ mots clean


.. note::
    You can generate a Bugzilla API key in your User Preferences page under the `API Keys <https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey>`_ tab.

.. note::
    A Bugzilla API key is required to allow mots to query Bugzilla for user information.


Validating ``mots.yaml``
~~~~~~~~~~~~~~~~~~~~~~~~
Validating your modules ensures that you have all the required keys in your configuration file, and that you have unique machine names for all your modules and submodules. Run the following command to do automatic validation:

.. code-block:: shell

    $ mots validate

Any modules or submodules that have errors in them will be included in any error output from this command.

Querying a File Path
~~~~~~~~~~~~~~~~~~~~
You can determine which module a file path belongs to by using the ``mots query`` command. This command takes an arbitrary number of path arguments, and prints out the modules on the screen.

.. code-block:: shell

	$ mots query example.text example_submodule/test2
	example.text:example
	example_submodule/test2:example_submodule


Exporting
~~~~~~~~~
Using the ``mots export`` command, the configuration can be exported in a different format. Currently only `reStructuredText` is supported. This command will output the result to standard output.

.. code-block:: shell

	$ mots export > mots.rst

The exported data will look like this:

.. code-block:: rst

	=======
	Modules
	=======

	Example
	~~~~~~
	This is an example module.

	.. list-table::
		:stub-columns: 1

		* - Owner(s)
		  - zeid
		* - Includes
		  - example.text

	Example Submodule
	=================

	This module is a submodule of the "Example" module.

	.. list-table::
		:stub-columns: 1

		* - Owner(s)
		  - zeid
		* - Peer(s)
		  - zeid
		* - Includes
		  - example_submodule/\*\*/\*

Debugging
~~~~~~~~~
To enable debug mode for any command, pass ``--debug`` before the command. For example:

.. code-block:: shell

	$ mots --debug query example.text

Developer Interface
===================

Module
~~~~~~
.. automodule:: mots.module
    :members:


Directory
~~~~~~~~~
.. automodule:: mots.directory
    :members:


CLI
~~~
.. automodule:: mots.cli
    :members:


Config
~~~~~~
.. automodule:: mots.config
    :members:


Utils
~~~~~
.. automodule:: mots.utils
    :members:


Development environment
=======================
To set up a local development environment, run the following commands. Replace the python version with the desired version on your local machine.

.. code-block:: shell

    make dev-env PY=python3.9
    make dev

The above commands will set up a local development environment using the provided python version available on your machine, and subsequently install all required packages in that environment.

Generate coverage report
~~~~~~~~~~~~~~~~~~~~~~~~

To generate a standard coverage report, run:

.. code-block:: shell

	make cov

To generate an html coverage report, run:

.. code-block:: shell

	make cov-html
	make serve-cov

Then navigate to your web browser.


Other make commands
~~~~~~~~~~~~~~~~~~~
Run `make` to see all available commands.

.. code-block:: shell

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
		test          run the test suite
