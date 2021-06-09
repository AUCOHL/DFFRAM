FROM efabless/openlane:v0.15

RUN python3 -m pip install click pyyaml

RUN curl -L https://github.com/google/verible/releases/download/v0.0-1278-g660b3d5/verible-v0.0-1278-g660b3d5-CentOS-7.9.2009-Core-x86_64.tar.gz | tar --strip-components 1 -xzC  /usr