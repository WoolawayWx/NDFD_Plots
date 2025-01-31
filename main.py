import subprocess
import downloadData
import os

# Ensure the script is run from the directory containing the script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

result = subprocess.run(["python3", "dataCheck.py"])
print(f"Child script exited with code: {result.returncode}")
if result.returncode == 200:
    print("Plotting Temperatures...")
    import TemperatureMap
    print("Plotting Sustained Winds...")
    import WindsMap
    print("Plotting Wind Gusts...")
    import WindGustsMap
    print("Plotting Rainfall Map...")
    import PrecipMap
    print("Plotting RH...")
    import RHMap
    print("Plotting Fire Danger Index...")
    import FireWeatherDangerIndex
    print("Uploading Files...")
    import supabaseFileUpload
    print('Done')
else:
    print('XML Data Error')
