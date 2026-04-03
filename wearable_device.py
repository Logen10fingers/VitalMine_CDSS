import requests
import time
import random
import sys

# CONFIGURATION
BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/login"
ADD_VITALS_URL = f"{BASE_URL}/add_vitals"

# SIMULATION SETTINGS
PATIENT_USERNAME = "Patient_Ben"
PASSWORD = "password123"


def get_virtual_vitals(scenario="stable"):
    """Generates fake sensor data based on a scenario."""
    if scenario == "stable":
        # 1. GREEN (STABLE): Normal ranges, avoiding all triggers.
        return {
            "temperature": round(random.uniform(36.5, 37.5), 1),
            "heart_rate": random.randint(70, 85),
            "resp_rate": random.randint(14, 18),
            "sys_bp": random.randint(110, 125),
            "dia_bp": random.randint(70, 80),
        }
    elif scenario == "sepsis":
        # 2. YELLOW (WARNING): High, but strictly avoids Red Critical thresholds.
        # Avoids: HR >= 130, Temp >= 39.5, RR >= 30, BP <= 90/60
        return {
            "temperature": round(random.uniform(38.2, 39.0), 1),
            "heart_rate": random.randint(105, 125),
            "resp_rate": random.randint(22, 28),
            "sys_bp": random.randint(100, 115),
            "dia_bp": random.randint(65, 75),
        }
    elif scenario == "hypothermia":
        # 3. RED (CRITICAL): Forces 'Code Blue' parameters in app.py.
        # Hits: Temp <= 35.0, HR <= 40, RR <= 8, BP <= 90/60
        return {
            "temperature": round(random.uniform(33.0, 34.5), 1),
            "heart_rate": random.randint(30, 38),
            "resp_rate": random.randint(6, 8),
            "sys_bp": random.randint(75, 85),
            "dia_bp": random.randint(45, 55),
        }


def start_simulation():
    print(f"--- 🏥 VitalMine IoT Simulator (Device ID: #VM-99) ---")
    print(f"Target Server: {BASE_URL}")

    # 1. Login to get the 'Session Cookie'
    session = requests.Session()
    try:
        print(">> Connecting to Hospital Network...")
        login_payload = {"username": PATIENT_USERNAME, "password": PASSWORD}
        response = session.post(LOGIN_URL, data=login_payload)

        if response.url == f"{BASE_URL}/login":  # If it stayed on login page, it failed
            print("❌ Authentication Failed! Check username/password.")
            sys.exit()
        print("✅ Device Paired Successfully!")

    except requests.exceptions.ConnectionError:
        print("❌ Error: VitalMine Server is not running! Run 'python app.py' first.")
        sys.exit()

    # 2. Infinite Loop of Data Transmission
    print("\nSelect Simulation Mode:")
    print("1. Healthy Recovery (Stable)")
    print("2. Sepsis Onset (Critical)")
    print("3. Hypothermia (Warning)")
    choice = input("Enter mode (1/2/3): ")

    mode_map = {"1": "stable", "2": "sepsis", "3": "hypothermia"}
    scenario = mode_map.get(choice, "stable")

    print(f"\n>> STARTED STREAMING DATA [{scenario.upper()}]...")
    print("Press CTRL+C to stop.\n")

    try:
        while True:
            # Generate Data
            data = get_virtual_vitals(scenario)
            data["name"] = PATIENT_USERNAME

            # Send to Server
            resp = session.post(ADD_VITALS_URL, data=data)

            if resp.status_code == 200:
                print(
                    f"📡 SENT: Temp={data['temperature']} | HR={data['heart_rate']} | RR={data['resp_rate']} | BP={data['sys_bp']}/{data['dia_bp']}"
                )
            else:
                print(f"⚠️ Transmission Error: {resp.status_code}")

            time.sleep(30)

    except KeyboardInterrupt:
        print("\n🛑 Simulation Stopped.")


if __name__ == "__main__":
    start_simulation()
