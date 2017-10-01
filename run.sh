#!/bin/bash

# exit the script on command errors or unset variables
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail
IFS=$'\n\t'

# https://stackoverflow.com/a/246128/295807
readonly script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "${script_dir}"

set +u
if [[ -z "${CONDA_DEFAULT_ENV}" || "$CONDA_DEFAULT_ENV" != "city_inquiry" ]]; then
    source activate city_inquiry
fi
set -u

source ~/Dropbox/Data/city_inquiry/api_keys.sh

# LOL
python run.py
