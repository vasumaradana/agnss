import requests
import os
import datetime

# Directory to store Ephemeris data
DATA_DIR = "ephemeris_data"
os.makedirs(DATA_DIR, exist_ok=True)

# NASA CDDIS is the primary source, but requires auth.
# For this demo, we will use a public FTP/HTTP mirror if available, or simulate the fetch.
# A common public source for broadcast ephemeris is the IGS (International GNSS Service).
# Example URL pattern: https://igs.bkg.bund.de/root_ftp/IGS/BRDC/2023/337/brdc3370.23n.gz (Daily GPS)

def fetch_daily_gps_ephemeris():
    """
    Fetches the current daily GPS broadcast ephemeris file (RINEX navigation).
    """
    now = datetime.datetime.utcnow()
    year = now.year
    doy = now.timetuple().tm_yday
    yy = str(year)[-2:]
    
    # Construct filename for today's broadcast ephemeris
    # Try RINEX 3 format first (standard for 2023+)
    # Format: BRD400DLR_S_YYYYDDD0000_01D_MN.rnx.gz
    # We need to try multiple sources/types as they might vary (WRD, IGS, DLR)
    
    rinex3_prefixes = ["BRDC00WRD_S", "BRDC00IGS_R", "BRD400DLR_S", "BRDM00DLR_S"]
    targets = []
    
    for prefix in rinex3_prefixes:
        filename = f"{prefix}_{year}{doy:03d}0000_01D_MN.rnx.gz"
        url = f"https://igs.bkg.bund.de/root_ftp/IGS/BRDC/{year}/{doy:03d}/{filename}"
        targets.append((filename, url))
    
    # Legacy RINEX 2 format (fallback)
    filename_r2 = f"brdc{doy:03d}0.{yy}n.gz"
    url_r2 = f"https://igs.bkg.bund.de/root_ftp/IGS/BRDC/{year}/{doy:03d}/{filename_r2}"
    targets.append((filename_r2, url_r2))
    
    # Try all targets
    for filename, url in targets:
        local_path = os.path.join(DATA_DIR, filename)
        
        # Check if file exists and is fresh (less than 1 hour old)
        if os.path.exists(local_path):
            file_age = datetime.datetime.now().timestamp() - os.path.getmtime(local_path)
            if file_age < 3600: # 1 hour in seconds
                print(f"File {filename} exists and is fresh ({int(file_age/60)} mins old).")
                return local_path
            else:
                print(f"File {filename} is stale ({int(file_age/60)} mins old). Re-downloading...")

        print(f"Fetching {filename} from {url}...")
        try:
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Successfully downloaded {filename}")
                return local_path
            else:
                print(f"Failed to download {filename}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching {filename}: {e}")
            
    # If we get here, all downloads failed
    # Fallback to dummy data (using the last attempted filename)
    local_path = os.path.join(DATA_DIR, "dummy_ephemeris.rnx.gz")
    # Fallback for demo if download fails
    print("Download failed. Creating dummy ephemeris file for demonstration.")
    import gzip
    with gzip.open(local_path, 'wt', encoding='utf-8') as f:
        f.write("""     2.10           N: GPS NAV DATA                         RINEX VERSION / TYPE
                                                            END OF HEADER
 1 25 12 04 12 00 00.0-4.600000000000E-04-1.000000000000E-11 0.000000000000E+00
    1.000000000000E+02 2.000000000000E+02 4.000000000000E-09 1.500000000000E+00
    3.000000000000E-06 5.000000000000E-03 6.000000000000E-06 5.153700000000E+03
    4.320000000000E+05 8.000000000000E-08-2.000000000000E+00 9.000000000000E-08
    9.500000000000E-01 2.500000000000E+02 1.500000000000E+00-7.000000000000E-09
    5.000000000000E-10 0.000000000000E+00 2.395000000000E+03 0.000000000000E+00
    2.000000000000E+00 0.000000000000E+00-5.000000000000E-09 1.000000000000E+02
    0.000000000000E+00 0.000000000000E+00 0.000000000000E+00 0.000000000000E+00
""")
    return local_path

if __name__ == "__main__":
    fetch_daily_gps_ephemeris()
