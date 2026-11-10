# Bambu printer monitor

A small tool for watching a Bambu Lab printer (built for the X2D) over your home network.
It reads the printer's live status (temperatures, layer, progress, error codes, AMS slots)
and grabs camera snapshots. A Claude session running on your computer can then read the
results and help diagnose a print.

It has to run on a computer on the **same network as the printer**. A cloud session can't
reach it.

## 1. Printer setup

On the printer's screen, open the network settings and note down:
- **IP address**
- **Access code** (the 8-character LAN code)
- **Serial number** (in the device info)

Recent Bambu firmware limits local access by third-party tools. If `status` below says
"Not authorized" or never receives data, turn on **LAN Only mode** and **Developer Mode** in
the printer's network settings. That disables cloud features such as remote printing from
Bambu Handy while it's on. Turn it back off when you're done.

## 2. Computer setup

```bash
pip install paho-mqtt
# ffmpeg is needed for the X-series camera:
#   macOS: brew install ffmpeg    Windows: winget install ffmpeg    Linux: apt install ffmpeg
```

Set the connection details as environment variables. Keep the access code out of git.

```bash
# macOS / Linux
export BAMBU_IP=192.168.1.50
export BAMBU_SERIAL=YOUR_SERIAL
export BAMBU_ACCESS_CODE=YOUR_CODE
```
```powershell
# Windows PowerShell
$env:BAMBU_IP="192.168.1.50"; $env:BAMBU_SERIAL="YOUR_SERIAL"; $env:BAMBU_ACCESS_CODE="YOUR_CODE"
```

## 3. Use it

```bash
python bambu_monitor.py status            # one-off summary
python bambu_monitor.py status --raw      # summary plus the full raw data
python bambu_monitor.py snapshot -o cam.jpg
python bambu_monitor.py watch             # log the whole print, snapshot every 60 s
python bambu_monitor.py watch --snap-every 20 --out wood_test
```

`watch` writes to a folder (default `print_log/`):
- `summary.txt`: the current state, readable at a glance
- `latest.json`: the full current state
- `status.jsonl`: every update with a timestamp, for reviewing the print afterwards
- `snap_*.jpg`: camera snapshots

Stop it with Ctrl+C.

## Using it with Claude

Run Claude on your computer in this folder, either in the Claude desktop app or with
`claude remote-control` in a terminal. Start `watch` in a separate terminal, then ask Claude
to look at `print_log/summary.txt` and the latest snapshots. For example, ask it to check the
first layer or the ironing pass, or to explain an error code.

## Notes

- The camera is tried in this order: RTSPS on port 322 (X1/H2/X2 series), then the JPEG
  stream on port 6000 (P1/A1 series). If both fail, enable **LAN mode liveview** on the
  printer.
- The printer uses a self-signed certificate, so certificate checks are turned off. Only
  use this tool on your own network.
- Tested against simulated printer servers, not a real X2D yet. Dual-nozzle fields may
  appear under `extruder` lines or only in `--raw` output.
