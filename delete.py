import os
import shutil
shutil.rmtree("tiles") if os.path.exists("tiles") else None
shutil.rmtree("worlds") if os.path.exists("worlds") else None