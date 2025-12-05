import requests

def check_day_152():
    # Day 152 of 2025
    # Format: BRD400DLR_S_YYYYDDD0000_01D_MN.rnx.gz
    filename = "BRD400DLR_S_20251520000_01D_MN.rnx.gz"
    url = f"https://igs.bkg.bund.de/root_ftp/IGS/BRDC/2025/152/{filename}"
    print(f"Checking: {url}")
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"SUCCESS: File {filename} exists.")
        else:
            print(f"FAILURE: File {filename} does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_day_152()
