FROM ubuntu:18.04

# Set timezone to UTC
RUN ln -snf /usr/share/zoneinfo/UTC /etc/localtime && echo UTC > /etc/timezone

RUN DEBIAN_FRONTEND=noninteractive apt update
RUN DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends git python3 python3-pip python3-setuptools python3-wheel python3-numpy python3-dotenv python3-matplotlib python3-tk

RUN pip3 install cbpro
