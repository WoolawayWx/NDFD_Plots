from flask import Flask, jsonify, request
import subprocess

app = Flask(__name__)

@app.route('/run_data_check', methods=['POST'])
def run_data_check():
    # Run the dataCheck.py script
    result = subprocess.run(["python3", "dataCheck.py"], capture_output=True, text=True)

    if result.returncode == 200:
        # If successful, run the plotting scripts
        try:
            import TemperatureMap
            import WindsMap
            import WindGustsMap
            import PrecipMap
            import RHMap
            import FireWeatherDangerIndex
            import supabaseFileUpload
            
            # You may want to include your actual plotting or uploading logic here
            
            return jsonify({"message": "All tasks completed successfully."}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "XML Data Error", "details": result.stderr}), 400

if __name__ == '__main__':
    app.run(debug=True)
