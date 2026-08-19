@ echo off
echo: >> C:\Scripts\weeds-processing\logWeedsProcessing.log
echo: >> C:\Scripts\weeds-processing\logWeedsProcessing.log
echo Process Started on %date% at %time% >> C:\Scripts\weeds-processing\logWeedsProcessing.log

echo Starting Weeds Processing at %date% %time% >> C:\Scripts\weeds-processing\logWeedsProcessing.log
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" "C:\Scripts\weeds-processing\agol_processes.py" >> C:\Scripts\weeds-processing\logWeedsProcessing.log
echo Scripts complete at %date% %time% >> C:\Scripts\weeds-processing\logWeedsProcessing.log