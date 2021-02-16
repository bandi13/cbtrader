FROM ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive apt update && apt install -y --no-install-recommends git python3 python3-pip python3-setuptools python3-wheel python3-numpy
RUN pip3 install cbpro
