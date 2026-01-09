@ echo off
echo: >> C:\Scripts\catchmentOps_AgolBackups\cOpsBackups\logAGOLbackups.log
echo: >> C:\Scripts\catchmentOps_AgolBackups\cOpsBackups\logAGOLbackups.log
echo Process Started on %date% at %time% >> C:\Scripts\catchmentOps_AgolBackups\cOpsBackups\logAGOLbackups.log

echo Starting River Management Backups at %date% %time% >> C:\Scripts\catchmentOps_AgolBackups\cOpsBackups\logAGOLbackups.log
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" "C:\Scripts\catchmentOps_AgolBackups\cOpsBackups\RMbackups.py" >> C:\Scripts\catchmentOps_AgolBackups\cOpsBackups\logAGOLbackups.log
echo Scripts complete at %date% %time% >> C:\Scripts\catchmentOps_AgolBackups\cOpsBackups\logAGOLbackups.log