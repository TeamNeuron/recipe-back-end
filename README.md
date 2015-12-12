# Recipe Back-end
This repository contains the back-end server code for Recipe Finder.

## Installation steps

First, ensure that you have [Python 2.7](https://www.python.org/) and [virtualenv](http://virtualenv.readthedocs.org/en/latest/installation.html) installed.

Next, setup virtualenv in the cloned git repository, and install required packages:

```bash
virtualenv -p /usr/bin/python2.7 venv
. venv/bin/activate
pip install Flask
pip install MetaMindApi --upgrade
```

## How to run server

```bash
. venv/bin/activate
python server.py
```
