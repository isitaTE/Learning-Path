FROM jupyter/base-notebook

USER root

# Update packages and install Git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER jovyan

