Development environment
-----------------------
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
		test          run the test suite
