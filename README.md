[Pelican](https://github.com/getpelican/pelican) ships with a Makefile with it's own `regenerate` method. This project aims to have the same functionality but additionally refresh the browser.

Installation
============

```shell
pip install git+https://github.com/ryneeverett/pelican_dev_server.git
```

Recommended
-----------

There is a required `--path` argument to the root of the pelican project which I recommend adding to a shell alias.

For instance, I use [autoenv](https://github.com/kennethreitz/autoenv) to manage my virtual environments, and have the something similar to the following in the `.env` file in my Pelican projects:

```shell
workon myproject
alias dev_server='pelican_dev_server -p $PWD/relative/path/to/project'
```

Help
====
```
$ pelican_dev_server --help
usage: pelican_dev_server [-h] -p PATH [-d] [-o [BROWSER]]

Development server for Pelican.

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to pelican project directory.
  -d, --debug
  -o [BROWSER], --open [BROWSER]
                        Open site, optionally specifying browser.
```
