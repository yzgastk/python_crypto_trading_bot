FROM ubuntu:latest

LABEL maintainer="olivier.decourbe@protonmail.com"
LABEL version="1.0"
LABEL description="Custom Docker image for Python Crypto Trading Bot"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt -y update
RUN apt install -y build-essential cmake wget git libgtest-dev
RUN apt install -y python3 python3-dev python3-pip

WORKDIR /home/pctb
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
RUN tar -xzf ta-lib-0.4.0-src.tar.gz
WORKDIR /home/pctb/ta-lib/
RUN ./configure --prefix=/usr
RUN make
RUN make install
RUN pip3 install TA-Lib

WORKDIR /home/pctb
RUN git clone https://github.com/yzgastk/python_crypto_trading_bot
RUN pip3 install -r ./python_crypto_trading_bot/requirements.txt
