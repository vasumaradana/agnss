import database
import ephemeris_fetcher
import requests
import time
import subprocess
import sys
import os

def test_db_lookup():
    print("Testing Database Lookup...")
    # Test with a known record from 310.csv
    # 1: GSM,310,260,51051,44473,0,-71.11,42.3588,1033,19,1,1459813819,1745016670,0
    result = database.get_cell_location(310, 260, 51051, 44473, "GSM")
    if result:
        print(f"SUCCESS: Found cell tower: {result}")
        assert abs(result['lat'] - 42.3588) < 0.0001
        assert abs(result['lon'] - -71.11) < 0.0001
    else:
        print("FAILURE: Cell tower not found.")
        sys.exit(1)

def test_ephemeris_fetch():
    print("\nTesting Ephemeris Fetcher...")
    path = ephemeris_fetcher.fetch_daily_gps_ephemeris()
    if path and os.path.exists(path):
        print(f"SUCCESS: Ephemeris file downloaded to {path}")
    else:
        print("FAILURE: Ephemeris fetch failed.")
        # Don't exit here as it might be a network issue, but note it.

def test_api_server():
    print("\nTesting API Server...")
    # Start server in background
    proc = subprocess.Popen([sys.executable, "server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5) # Wait for server to start
    
    try:
        # Test Location Endpoint
        payload = {"mcc": 310, "mnc": 260, "lac": 51051, "cid": 44473, "radio": "GSM"}
        resp = requests.post("http://localhost:8000/location", json=payload)
        if resp.status_code == 200:
            print(f"SUCCESS: API /location returned: {resp.json()}")
        else:
            print(f"FAILURE: API /location returned {resp.status_code}: {resp.text}")
            
        # Test Ephemeris Endpoint
        # Note: This might fail if the fetcher failed earlier or network is down, but we check if it runs.
        resp = requests.get("http://localhost:8000/ephemeris/current")
        if resp.status_code == 200 or resp.status_code == 503:
            print(f"SUCCESS: API /ephemeris/current responded with {resp.status_code}")
        else:
            print(f"FAILURE: API /ephemeris/current returned {resp.status_code}")
            
    except Exception as e:
        print(f"FAILURE: API Test Exception: {e}")
    finally:
        proc.terminate()

if __name__ == "__main__":
    test_db_lookup()
    test_ephemeris_fetch()
    test_api_server()
