from flask import Flask, render_template, request, jsonify
import threading
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, IAudioMeterInformation

app = Flask(__name__)

# Shared configuration
CONFIG = {
    "enabled": True,
    "threshold": 0.70,        # 70% peak audio limit
    "safe_level": 0.30,       # 30% master volume drop
    "current_peak": 0.0       # Live monitoring data
}

def audio_shield_loop():
    print("🛡️ Ear Shield background thread active.")
    import comtypes
    comtypes.CoInitialize()
    
    danger_start_time = None
    
    try:
        devices = AudioUtilities.GetSpeakers()
        
        # --- THE FIX: Unwrap the new AudioDevice box if necessary ---
        if hasattr(devices, 'Activate'):
            raw_device = devices
        else:
            raw_device = devices._dev # This extracts the hidden raw COM pointer
            
        # Now we can safely activate the meters
        meter_interface = raw_device.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
        meter = cast(meter_interface, POINTER(IAudioMeterInformation))
        
        volume_interface = raw_device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_control = cast(volume_interface, POINTER(IAudioEndpointVolume))
        
        print("✅ Successfully connected to Windows Default Audio!")

        while True:
            if CONFIG["enabled"]:
                # Grab the live peak volume
                CONFIG["current_peak"] = round(meter.GetPeakValue(), 3)
                
                # Check against our custom slider limit
                if CONFIG["current_peak"] >= CONFIG["threshold"]:
                    if danger_start_time is None:
                        danger_start_time = time.time()
                    
                    # 0.2 second lightning fast trigger
                    if time.time() - danger_start_time >= 0.2: 
                        print(f"⚠️ Peak {CONFIG['current_peak']} exceeded limit {CONFIG['threshold']}! Dropping volume.")
                        volume_control.SetMasterVolumeLevelScalar(CONFIG["safe_level"], None)
                        danger_start_time = None
                        time.sleep(1.5) # Pause to let the user realize volume dropped
                else:
                    danger_start_time = None
            else:
                CONFIG["current_peak"] = 0.0
                danger_start_time = None
                
            time.sleep(0.1) # Check 10 times a second
            
    except Exception as e:
        print(f"\n❌ AUDIO CRASH ERROR: {e}\n")
        CONFIG["current_peak"] = 0.0

# Start the background thread
audio_thread = threading.Thread(target=audio_shield_loop, daemon=True)
audio_thread.start()

@app.route('/')
def index():
    return render_template('index.html', config=CONFIG)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    data = request.json
    CONFIG["enabled"] = data.get("enabled", CONFIG["enabled"])
    CONFIG["threshold"] = float(data.get("threshold", CONFIG["threshold"])) / 100
    CONFIG["safe_level"] = float(data.get("safe_level", CONFIG["safe_level"])) / 100
    return jsonify({"status": "success", "config": CONFIG})

@app.route('/get_live_data')
def get_live_data():
    return jsonify({"peak": CONFIG["current_peak"]})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)