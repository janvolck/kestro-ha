#!/bin/bash
script=$(realpath $0)
script_dir=$(dirname $script)
python_dir=${script_dir}/python

cd ${python_dir}
python -m kestro