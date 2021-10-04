#!/usr/bin/env bash

source ./venv/Scripts/activate

docker build -t sccrpt .

aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 985118252342.dkr.ecr.us-west-1.amazonaws.com/sccrpt

docker tag sccrpt:latest 985118252342.dkr.ecr.us-west-1.amazonaws.com/sccrpt:latest

docker push 985118252342.dkr.ecr.us-west-1.amazonaws.com/sccrpt:latest
