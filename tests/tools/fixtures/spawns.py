import subprocess
import time
from pathlib import Path


def make(client, params):
    child = subprocess.Popen(["sleep", "3600"])
    Path(params["pid_file"]).write_text(str(child.pid))
    time.sleep(3600)
