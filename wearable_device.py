import requests
import time
import random
import sys

# CONFIGURATION
BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/login"
ADD_VITALS_URL = f"{BASE_URL}/add_vitals"

# SIMULATION SETTINGS
PATIENT_USERNAME = "patient_om"
PASSWORD = "password123"


def get_virtual_vitals(scenario="stable"):
    """Generates fake sensor data based on a scenario."""
    if scenario == "stable":
        return {
            "temperature": round(random.uniform(36.1, 37.2), 1),
            "heart_rate": random.randint(60, 90),
            "resp_rate": random.randint(12, 18),
            "wbc_count": random.randint(5000, 10000),
        }
    elif scenario == "sepsis":
        return {
            "temperature": round(random.uniform(38.5, 40.5), 1),
            "heart_rate": random.randint(100, 140),
            "resp_rate": random.randint(22, 35),
            "wbc_count": random.randint(13000, 20000),
        }
    elif scenario == "hypothermia":
        return {
            "temperature": round(random.uniform(34.0, 35.8), 1),
            "heart_rate": random.randint(50, 65),
            "resp_rate": random.randint(10, 14),
            "wbc_count": random.randint(4000, 9000),
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

            # Send to Server
            # Note: We need to send 'name' because the backend expects it,
            # but since we are logged in as patient, the backend logic handles it.
            data["name"] = PATIENT_USERNAME

            resp = session.post(ADD_VITALS_URL, data=data)

            if resp.status_code == 200:
                print(
                    f"📡 SENT: Temp={data['temperature']} | HR={data['heart_rate']} | Status: {resp.url.split('/')[-1]}"
                )
            else:
                print(f"⚠️ Transmission Error: {resp.status_code}")

            time.sleep(30)  # Wait 30 seconds before next reading

    except KeyboardInterrupt:
        print("\n🛑 Simulation Stopped.")


if __name__ == "__main__":
    start_simulation()
