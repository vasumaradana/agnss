import requests

def check_file(doy):
    filename = f"brdc{doy:03d}0.25n.gz"
    url = f"https://igs.bkg.bund.de/root_ftp/IGS/BRDC/2025/{doy:03d}/{filename}"
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
    print("Checking Yesterday (337)...")
    check_file(337)
    print("\nChecking Today (338)...")
    check_file(338)
