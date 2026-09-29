@echo off
set PYTHONPATH=%~dp0src;%PYTHONPATH%
py -3.13 -m vh.cli %*
