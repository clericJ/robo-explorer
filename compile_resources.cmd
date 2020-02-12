@echo off
setlocal enableextensions

cd ui
pyuic5.exe gamewindow.ui -o gamewindow.py
