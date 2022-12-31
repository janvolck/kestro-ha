#!/bin/bash

script=$(realpath $0)
script_dir=$(dirname $script)
angular_dir=${script_dir}/angular
python_dir=${script_dir}/python
current_dir=$(pwd)

cd ${angular_dir}
# ng build --configuration=raspberrypi
ng build

rc=$?
if [ ! $rc ]; then
    echo "failed to build angular"
    cd ${current_dir}
    exit 1
fi


echo "frontend build finished"
rm -rf ${python_dir}/kestro/webapp/templates/*
rm -rf ${python_dir}/kestro/webapp/static/*

mv ${angular_dir}/dist/frontend/index.html ${python_dir}/kestro/webapp/templates/
mv ${angular_dir}/dist/frontend/* ${python_dir}/kestro/webapp/static/

cd ${python_dir}

pip3 install .
rc=$?
if [ ! $rc ]; then
    echo "failed to build python"
    cd ${current_dir}
    exit 1
fi

echo "python build finished"
cd ${current_dir}