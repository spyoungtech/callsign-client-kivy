FROM python:3.11-slim
RUN apt update && apt install -y zlib1g-dev git openjdk-17-jdk unzip zip android-sdk curl sdkmanager build-essential autoconf libffi-dev libtool libssl-dev ccache cmake libltdl-dev patch pkg-config automake
ENV ANDROID_HOME=/usr/lib/android-sdk

RUN pip install buildozer cython
RUN yes | sdkmanager --licenses

RUN useradd -m -u 1000 builder
USER builder

WORKDIR /opt/build

COPY buildozer.spec /opt/build/buildozer.spec
COPY callsigns_kivy /opt/build/callsigns_kivy

RUN buildozer android debug
