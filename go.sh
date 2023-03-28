#!/bin/bash

cd pkgs

if pip list | grep -q andes; then
    echo "ANDES is already installed."
else
    echo "ANDES is not installed. Cloning and installing..."
    git clone -b develop https://github.com/CURENT/andes.git
    git checkout develop
    cd andes
    pip install -r requirements.txt
    pip install -e .
    cd ..
fi

if pip list | grep -q agvis; then
    echo "AGVis is already installed."
else
    echo "AGVis is not installed. Cloning and installing..."
    git clone -b develop https://github.com/CURENT/agvis.git
    git checkout develop
    cd agvis
    pip install -r requirements.txt
    pip install -e .
    cd ..
fi

cd ..

echo "ANDES permeable:"
andes

echo "AGVis permeable:"
agvis

exit
