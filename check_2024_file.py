import requests

def check_2024_file():
    # Day 338 of 2024 (Dec 3rd/4th 2024)
    filename = "brdc3380.24n.gz"
    url = f"https://igs.bkg.bund.de/root_ftp/IGS/BRDC/2024/338/{filename}"
    print(f"Checking: {url}")
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"SUCCESS: File {filename} exists (Real world is 2024).")
        else:
            print(f"FAILURE: File {filename} does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_2024_file()
