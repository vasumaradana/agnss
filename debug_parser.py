import requests
import gzip
import shutil

def inspect_rinex3():
    # Download the specific file that is failing to parse
    url = "https://igs.bkg.bund.de/root_ftp/IGS/BRDC/2025/338/BRDC00WRD_S_20253380000_01D_MN.rnx.gz"
    local_filename = "debug_file.rnx.gz"
    
    print(f"Downloading {url}...")
    resp = requests.get(url)
    with open(local_filename, 'wb') as f:
        f.write(resp.content)
        
    print("Scanning for first GPS record...")
    with gzip.open(local_filename, 'rt', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.startswith('G'):
                print(f"Found GPS record at line {i+1}:")
                print(line.strip())
                break

if __name__ == "__main__":
    inspect_rinex3()
