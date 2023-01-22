#!/bin/bash
script=$(realpath $0)
script_dir=$(dirname $script)
python_dir=${script_dir}/python

pip3 show debugpy
rc=$?
if [[ "$rc" == "1" ]]; then
    pip3 install debugpy
fi

cd ${python_dir}
python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m kestro