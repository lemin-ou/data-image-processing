#!/bin/bash
echo "creating necessary directories"
mkdir -p data/extracted
echo "installing dependencies ...."
pip3 install --upgrade -r requirements.txt
echo "build libsvm for all target ...."
cd processimage/libsvm/ && make -B
echo "build libsvm for python ...."
cd python && make
echo "All successfully done."
