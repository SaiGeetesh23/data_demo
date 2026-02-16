# download_argo.py

from ftplib import FTP
import os

FTP_SERVER = "ftp.ifremer.fr"
REMOTE_DIR = "/ifremer/argo/dac"
LOCAL_DIR = "./FloatDATA/2026"

os.makedirs(LOCAL_DIR, exist_ok=True)

ftp = FTP(FTP_SERVER)
ftp.login()

ftp.cwd(REMOTE_DIR)
dac_folders = ftp.nlst()

for dac in dac_folders[:3]:   # limit to reduce load (demo safe)
    try:
        ftp.cwd(dac)
        float_dirs = ftp.nlst()

        for float_id in float_dirs[:5]:
            ftp.cwd(float_id)
            files = ftp.nlst()

            for f in files:
                if f.endswith(".nc"):
                    local_path = os.path.join(LOCAL_DIR, f)
                    if not os.path.exists(local_path):
                        with open(local_path, "wb") as fp:
                            ftp.retrbinary(f"RETR {f}", fp.write)

            ftp.cwd("..")

        ftp.cwd("..")

    except:
        ftp.cwd("..")

ftp.quit()

print("Download complete.")
