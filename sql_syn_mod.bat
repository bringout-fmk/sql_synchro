c:
cd \sql_synchro

echo -------------------------------------- > LOG\info_%2.log
echo Trenutni user je %USERNAME% >> LOG\info_%2.log
echo -------------------------------------- >> LOG\info_%2.log 
echo Datum: >> LOG\info_%2.log 
date /t >> LOG\info_%1.log
time /t >> LOG\info_%1.log
echo -------------------------------------- >> LOG\info_%2.log 
c:\python25\python.exe sql_synchro.py %1 >> LOG\info_%1.log

echo --------**************---kraj operacije-************--------------------------- >> LOG\info_%1.log 
