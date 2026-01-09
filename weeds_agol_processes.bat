@ echo off
echo: >> C:\Scripts\weedsProcessing\logWeedsProcessing.log
echo: >> C:\Scripts\weedsProcessing\logWeedsProcessing.log
echo Process Started on %date% at %time% >> C:\Scripts\weedsProcessing\logWeedsProcessing.log

echo Starting Weeds Processing at %date% %time% >> C:\Scripts\weedsProcessing\logWeedsProcessing.log
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" "C:\Scripts\weedsProcessing\agol_processes.py" >> C:\Scripts\weedsProcessing\logWeedsProcessing.log
echo Scripts complete at %date% %time% >> C:\Scripts\weedsProcessing\logWeedsProcessing.log