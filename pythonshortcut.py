import os
import sys
from pathlib import Path
import win32com.client

def create_shortcut(script_path, shortcut_path):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    pythonw_path = Path(sys.executable).with_name('pythonw.exe')
    shortcut.TargetPath = str(pythonw_path)
    shortcut.Arguments = f'"{script_path}"'
    shortcut.WorkingDirectory = str(os.path.dirname(script_path))
    shortcut.IconLocation = str(pythonw_path)
    shortcut.save()

def add_to_startup(script_path):
    startup_dir = Path(os.getenv('APPDATA')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    shortcut_path = startup_dir / f'{Path(script_path).stem}.lnk'
    create_shortcut(script_path, shortcut_path)
    print(f"Shortcut created at {shortcut_path}")

if __name__ == "__main__":
    script_path = Path(__file__).resolve()
    add_to_startup(script_path)