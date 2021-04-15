#!/bin/bash

echo $PATH

export PATH="$PATH:/usr/local/bin" # Make sure that chromedriver is in PATH
# Make the virtualenv work properly
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=$HOME/.local/pipx/venvs/virtualenvwrapper/bin/python3
source $HOME/.local/bin/virtualenvwrapper.sh

workon news-snapshots
if [ $# -eq 0 ]; then
    python snapshot.py --defaults
elif [ $1 == "full_archive" ]; then
    python snapshot.py -s -a --defaults
fi
deactivate