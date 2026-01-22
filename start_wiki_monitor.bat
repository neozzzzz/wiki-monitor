@echo off
set OPENSSL_CONF=%~dp0openssl.cnf
set PYTHONHTTPSVERIFY=0
set CURL_CA_BUNDLE=
set REQUESTS_CA_BUNDLE=
start "" "%~dp0wiki_monitor.exe"