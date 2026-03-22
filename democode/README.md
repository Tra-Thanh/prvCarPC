
# CarPC CAN Demo

A cross-platform Python demo simulating the CAN bus architecture for CarPC. Runs on both Windows and Linux (including WSL).

## 🚀 Features

- **Cross-platform**: Works on Windows, Linux, and WSL
- **No hardware required**: Supports virtual CAN simulation or SocketCAN
- **DBC decoding**: Decodes CAN signals using a DBC file
- **Threading**: Ensures multi-platform compatibility

## 📋 Requirements

- Python 3.8+
- `python-can`, `cantools` (install via pip)
- (Linux/WSL) To test with SocketCAN: `can-utils`

## 🔧 Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd prvCarPC/democode
```

### 2. (Recommended) Create a virtual environment

**Linux/WSL/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
pip install python-can cantools
```

### 4. (Optional) Create a virtual CAN interface on Linux/WSL

If you want to run with SocketCAN (can0):

```bash
sudo apt update
sudo apt install can-utils
sudo modprobe vcan
sudo ip link add dev can0 type vcan
sudo ip link set up can0
```
Then, open `can_demo.py` and set:
```python
USE_SOCKETCAN = True
```

## ▶️ Run Demo

```bash
python can_demo.py
```
- If `USE_SOCKETCAN = False` (default): runs simulation on both Windows and Linux.
- If `USE_SOCKETCAN = True`: uses can0 (SocketCAN) on Linux/WSL.

## 📁 Project Structure

- `can_demo.py`: Main demo script
- `dbc/vehicle.dbc`: DBC file for CAN decoding
- `can_frames.jsonl`: Output log file
- `demo_log.txt`: Detailed log

## 📝 Notes

- Do **not** commit `.venv` to git (add it to `.gitignore`)
- If you have a `requirements.txt` file, you can install with:  
  `pip install -r requirements.txt`
- Ensure `dbc/vehicle.dbc` exists in the correct location
- To stop the demo: press Ctrl+C

## ❓ Troubleshooting

- **ImportError**: Check if all required packages are installed
- **DBC file not found**: Verify the path and file existence
- **Permission denied (Linux)**: You may need `chmod +x can_demo.py`

---
For any issues, check the comments in `can_demo.py` or contact the maintainer.
