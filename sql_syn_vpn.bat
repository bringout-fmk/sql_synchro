@echo off
ping /n 1 %1 | find "Reply" >nul
if %errorlevel% == 0 goto reply
@echo IP %1 : prodavnica %2 : nema odgovora !!!! Pokusajte ponovo.
goto end
:reply
ping /n 1 %1 | find "unreachable" >nul
if %errorlevel% == 0 goto unreach
@echo IP %1 : prodavnica %2 : ping uspjesan... idemo na sinhronizaciju.
sql_synvpn.py /VPN %1 %2
goto end
:unreach
@echo IP %1 : prodavnica %2 : prodavnica nije konektovana na VPN !!!
:end
