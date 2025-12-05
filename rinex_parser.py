import gzip
import datetime
import math

def parse_rinex_nav(file_path):
    """
    Parses a RINEX 2 or 3 Navigation file (GPS) and returns a list of dictionaries,
    where each dictionary represents the ephemeris for one satellite.
    
    This is a simplified parser focused on extracting the fields required for
    Nordic nrf_modem_gnss_agnss_gps_data_ephemeris.
    """
    ephemeris_data = []
    
    try:
        if file_path.endswith('.gz'):
            f = gzip.open(file_path, 'rt', encoding='utf-8')
        else:
            f = open(file_path, 'r', encoding='utf-8')
            
        with f:
            lines = f.readlines()
            
        # Skip header
        header_end_idx = 0
        version = 2.0
        for i, line in enumerate(lines):
            if "RINEX VERSION / TYPE" in line:
                try:
                    version = float(line[:9].strip())
                except:
                    pass
            if "END OF HEADER" in line:
                header_end_idx = i + 1
                break
                
        # Parse data blocks
        i = header_end_idx
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
                
            # RINEX 3: G01 2025 12 04 12 00 00 ...
            # RINEX 2:  1 25 12 04 12 00 00 ...
            
            is_gps = False
            sv_id = 0
            
            try:
                # Replace 'D' with 'E' for scientific notation
                line = line.replace('D', 'E')
                
                if version >= 3.0:
                    # RINEX 3 format
                    prn_str = line[:3].strip()
                    if prn_str.startswith('G'):
                        is_gps = True
                        sv_id = int(prn_str[1:])
                    else:
                        # Skip non-GPS records (R=Glonass, E=Galileo, C=Beidou, J=QZSS)
                        # We need to skip the correct number of lines for this record type
                        # But simpler is just to scan for next start of record
                        i += 1
                        continue
                else:
                    # RINEX 2 format
                    prn_str = line[:2].strip()
                    try:
                        sv_id = int(prn_str)
                        is_gps = True # Assume GPS for RINEX 2 NAV
                    except:
                        i += 1
                        continue

                if not is_gps:
                    i += 1
                    continue

                # We need to read 8 lines for one GPS record (RINEX 2 and 3 usually same for GPS)
                if i + 7 >= len(lines):
                    break
                    
                record_lines = [lines[i+j].replace('D', 'E') for j in range(8)]
                
                # Parse fields (Fixed width usually 19 chars)
                # Helper to extract float
                def get_float(line_idx, start, length):
                    val_str = record_lines[line_idx][start:start+length].strip()
                    if not val_str: return 0.0
                    return float(val_str)

                # Data mapping based on RINEX 2.10 / 3.0 format
                # Line 1: PRN, Epoch, SV Clock Bias, SV Clock Drift, SV Clock Drift Rate
                
                # RINEX 3 offsets are slightly different for Line 1
                if version >= 3.0:
                    # RINEX 3
                    # PRN (0-3), Year (4-8), Month (9-11), Day (12-14), Hour (15-17), Min (18-20), Sec (21-23)
                    # af0 starts at 23
                    af0 = get_float(0, 23, 19)
                    af1 = get_float(0, 42, 19)
                    af2 = get_float(0, 61, 19)
                else:
                    # RINEX 2
                    af0 = get_float(0, 22, 19)
                    af1 = get_float(0, 41, 19)
                    af2 = get_float(0, 60, 19)
                
                # Line 2: IODE, Crs, Delta n, M0
                # Subsequent lines usually start at index 4 (indent) for RINEX 3, index 3 for RINEX 2
                # But get_float(..., 3, 19) usually works for both if there is padding.
                # Let's check if we need to adjust.
                # RINEX 2: 3, 22, 41, 60
                # RINEX 3: 4, 23, 42, 61 (likely shifted by 1 due to wider PRN column in header?)
                # Actually, standard RINEX 3 broadcast orbit lines:
                #    BroadCast Orbit - 1                                                                 
                #      IODE, Crs, Delta n, M0
                #      (4X,4D19.12)
                # So they start at index 4.
                
                base_idx = 4 if version >= 3.0 else 3
                
                iode = get_float(1, base_idx, 19)
                crs = get_float(1, base_idx + 19, 19)
                delta_n = get_float(1, base_idx + 38, 19)
                m0 = get_float(1, base_idx + 57, 19)
                
                # Line 3: Cuc, e, Cus, sqrt(A)
                cuc = get_float(2, base_idx, 19)
                e = get_float(2, base_idx + 19, 19)
                cus = get_float(2, base_idx + 38, 19)
                sqrt_a = get_float(2, base_idx + 57, 19)
                
                # Line 4: Toe, Cic, Omega0, Cis
                toe = get_float(3, base_idx, 19)
                cic = get_float(3, base_idx + 19, 19)
                omega0 = get_float(3, base_idx + 38, 19)
                cis = get_float(3, base_idx + 57, 19)
                
                # Line 5: i0, Crc, omega, OmegaDot
                i0 = get_float(4, base_idx, 19)
                crc = get_float(4, base_idx + 19, 19)
                omega = get_float(4, base_idx + 38, 19)
                omega_dot = get_float(4, base_idx + 57, 19)
                
                # Line 6: IDOT, Codes on L2, GPS Week, L2 P data flag
                idot = get_float(5, base_idx, 19)
                gps_week = get_float(5, base_idx + 38, 19) # Skip Codes on L2
                
                # Line 7: SV Accuracy, SV Health, TGD, IODC
                sv_health = get_float(6, base_idx + 19, 19)
                tgd = get_float(6, base_idx + 38, 19)
                iodc = get_float(6, base_idx + 57, 19)
                
                eph = {
                    "sv_id": sv_id,
                    "iode": int(iode),
                    "iodc": int(iodc),
                    "toc": 0, 
                    "toe": int(toe),
                    "af0": af0,
                    "af1": af1,
                    "af2": af2,
                    "crs": crs,
                    "delta_n": delta_n,
                    "m0": m0,
                    "cuc": cuc,
                    "cus": cus,
                    "crc": crc,
                    "cis": cis,
                    "cic": cic,
                    "i0": i0,
                    "idot": idot,
                    "omega0": omega0,
                    "omega_dot": omega_dot,
                    "sqrt_a": sqrt_a,
                    "e": e,
                    "w": omega, 
                    "health": int(sv_health),
                    "tgd": tgd,
                    "week": int(gps_week)
                }
                
                ephemeris_data.append(eph)
                
                # Move to next record
                i += 8
                
            except Exception as e:
                print(f"Error parsing line {i}: {e}")
                i += 1 # Try to recover
                
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    return ephemeris_data

if __name__ == "__main__":
    # Test with dummy file if exists
    import os
    if os.path.exists("ephemeris_data/brdc3380.25n.gz"):
        data = parse_rinex_nav("ephemeris_data/brdc3380.25n.gz")
        print(f"Parsed {len(data)} satellites.")
        if data:
            print(data[0])
