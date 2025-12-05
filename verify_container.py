import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def wait_for_server():
    print("Waiting for server to start...")
    for i in range(30):
        try:
            resp = requests.get(f"{BASE_URL}/docs")
            if resp.status_code == 200:
                print("Server is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("Server failed to start.")
    return False

def test_location():
    print("\nTesting /location endpoint...")
    payload = {"mcc": 310, "mnc": 260, "lac": 51051, "cid": 44473, "radio": "GSM"}
    try:
        resp = requests.post(f"{BASE_URL}/location", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            print(f"SUCCESS: {data}")
            assert 'lat' in data
            assert 'lon' in data
        else:
            print(f"FAILURE: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"FAILURE: {e}")

def test_ephemeris_current():
    print("\nTesting /ephemeris/current endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/ephemeris/current")
        if resp.status_code == 200:
            print(f"SUCCESS: Received {len(resp.content)} bytes")
        elif resp.status_code == 503:
            print("WARNING: Ephemeris unavailable (expected if download fails in container without internet/auth)")
        else:
            print(f"FAILURE: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"FAILURE: {e}")

def test_ephemeris_nordic():
    print("\nTesting /ephemeris/nordic endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/ephemeris/nordic")
        if resp.status_code == 200:
            data = resp.json()
            if data['status'] == 'success':
                print(f"SUCCESS: Received {len(data['data'])} satellite records")
            else:
                print(f"FAILURE: API returned error status: {data}")
        elif resp.status_code == 503:
             print("WARNING: Ephemeris unavailable")
        else:
            print(f"FAILURE: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    if wait_for_server():
        test_location()
        test_ephemeris_current()
        test_ephemeris_nordic()
    else:
        sys.exit(1)
