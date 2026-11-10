#!/usr/bin/env python3
"""Local monitor for a Bambu Lab printer (built for the X2D) over LAN.

Reads live status (temps, layer, progress, HMS error codes) over the printer's
local MQTT connection and grabs camera snapshots, so a local Claude session
(or you) can inspect a print in progress.

Configuration comes from environment variables (never commit these):
  BAMBU_IP           printer IP address, e.g. 192.168.1.50
  BAMBU_SERIAL       printer serial number
  BAMBU_ACCESS_CODE  LAN access code shown on the printer screen

Commands:
  status                one-shot summary of the printer's current state
  snapshot [-o FILE]    save one camera frame as JPEG
  watch [--interval N] [--snap-every N] [--out DIR]
                        log every status report to DIR/status.jsonl, keep
                        DIR/latest.json and DIR/summary.txt up to date, and
                        save a snapshot every N seconds
"""

import argparse
import json
import os
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency: pip install paho-mqtt")

MQTT_PORT = 8883
RTSP_PORT = 322     # X1 / H2 / X2 series camera (RTSPS)
JPEG_PORT = 6000    # P1 / A1 series camera (TLS JPEG stream)
USER = "bblp"


def config():
    missing = [k for k in ("BAMBU_IP", "BAMBU_SERIAL", "BAMBU_ACCESS_CODE") if not os.environ.get(k)]
    if missing:
        sys.exit("Set these environment variables first: " + ", ".join(missing))
    return os.environ["BAMBU_IP"], os.environ["BAMBU_SERIAL"], os.environ["BAMBU_ACCESS_CODE"]


def insecure_tls():
    # The printer uses a self-signed certificate on the local network.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def deep_merge(dst, src):
    """Printers often send partial updates; merge them into one state."""
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def hms_code(entry):
    attr, code = int(entry.get("attr", 0)), int(entry.get("code", 0))
    return "%04X_%04X_%04X_%04X" % (attr >> 16, attr & 0xFFFF, code >> 16, code & 0xFFFF)


def fmt_minutes(m):
    try:
        m = int(m)
    except (TypeError, ValueError):
        return "?"
    return f"{m // 60}h{m % 60:02d}m"


def summarize(state):
    """Human-readable summary of the merged 'print' state."""
    p = state.get("print", {})
    lines = [f"time:      {datetime.now().isoformat(timespec='seconds')}"]
    lines.append(f"job:       {p.get('subtask_name') or p.get('gcode_file') or '-'}")
    lines.append(f"state:     {p.get('gcode_state', '?')}  stage: {p.get('mc_print_stage', '?')}")
    lines.append(f"progress:  {p.get('mc_percent', '?')}%  layer {p.get('layer_num', '?')}/{p.get('total_layer_num', '?')}"
                 f"  remaining {fmt_minutes(p.get('mc_remaining_time'))}")
    def t(cur, tgt):
        c, g = p.get(cur), p.get(tgt)
        return f"{c if c is not None else '?'}/{g if g is not None else '?'}C"
    lines.append(f"nozzle:    {t('nozzle_temper', 'nozzle_target_temper')}  bed: {t('bed_temper', 'bed_target_temper')}"
                 f"  chamber: {p.get('chamber_temper', '?')}C")
    # Dual-nozzle printers (H2D/X2D) may report per-extruder data here.
    ext = (p.get("device") or {}).get("extruder") or {}
    for i, e in enumerate(ext.get("info") or []):
        if isinstance(e, dict):
            lines.append(f"extruder{i}: {json.dumps(e, separators=(',', ':'))[:160]}")
    for key in ("spd_lvl", "fan_gear", "cooling_fan_speed", "heatbreak_fan_speed"):
        if key in p:
            lines.append(f"{key}: {p[key]}")
    if p.get("print_error"):
        lines.append(f"print_error: {p['print_error']}")
    hms = p.get("hms") or []
    if hms:
        for h in hms:
            c = hms_code(h)
            lines.append(f"HMS {c}  https://wiki.bambulab.com/en/x1/troubleshooting/hmscode/{c}")
    else:
        lines.append("HMS: none")
    ams = (p.get("ams") or {}).get("ams") or []
    for unit in ams:
        for tray in unit.get("tray", []):
            if tray.get("tray_type"):
                lines.append(f"AMS{unit.get('id')} slot{tray.get('id')}: {tray.get('tray_type')} "
                             f"#{tray.get('tray_color', '')[:6]} {tray.get('tray_sub_brands', '')}".rstrip())
    return "\n".join(lines)


class Printer:
    def __init__(self, ip, serial, code):
        self.ip, self.serial, self.code = ip, serial, code
        self.state = {}
        self.lock = threading.Lock()
        self.got_report = threading.Event()
        self.on_report = None
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"monitor-{os.getpid()}")
        self.client.username_pw_set(USER, code)
        self.client.tls_set_context(insecure_tls())
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            print(f"MQTT connect failed: {reason_code} (check access code / LAN mode)", file=sys.stderr)
            return
        client.subscribe(f"device/{self.serial}/report")
        self.request_full_status()

    def request_full_status(self):
        msg = {"pushing": {"sequence_id": "0", "command": "pushall"}}
        self.client.publish(f"device/{self.serial}/request", json.dumps(msg))

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload)
        except ValueError:
            return
        with self.lock:
            deep_merge(self.state, data)
            snapshot = json.loads(json.dumps(self.state))
        self.got_report.set()
        if self.on_report:
            self.on_report(data, snapshot)

    def start(self):
        self.client.connect(self.ip, MQTT_PORT, keepalive=60)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


def snapshot_rtsp(ip, code, out):
    url = f"rtsps://{USER}:{code}@{ip}:{RTSP_PORT}/streaming/live/1"
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-rtsp_transport", "tcp", "-i", url,
           "-frames:v", "1", "-q:v", "2", out]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=20)
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not installed (needed for the X-series camera)")
    except subprocess.TimeoutExpired:
        raise RuntimeError("RTSP camera timed out")
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError("RTSP snapshot failed: " + r.stderr.decode(errors="replace").strip()[-300:])


def snapshot_jpeg_port(ip, code, out):
    auth = struct.pack("<IIII", 0x40, 0x3000, 0, 0)
    auth += USER.encode().ljust(32, b"\0") + code.encode().ljust(32, b"\0")
    with socket.create_connection((ip, JPEG_PORT), timeout=10) as raw:
        with insecure_tls().wrap_socket(raw, server_hostname=ip) as s:
            s.sendall(auth)
            def read(n):
                buf = b""
                while len(buf) < n:
                    chunk = s.recv(n - len(buf))
                    if not chunk:
                        raise RuntimeError("camera stream closed")
                    buf += chunk
                return buf
            header = read(16)
            size = int.from_bytes(header[0:3], "little")
            img = read(size)
    if not img.startswith(b"\xff\xd8"):
        raise RuntimeError("camera returned data that is not a JPEG")
    with open(out, "wb") as f:
        f.write(img)


def snapshot(ip, code, out):
    errors = []
    for fn in (snapshot_rtsp, snapshot_jpeg_port):
        try:
            fn(ip, code, out)
            return out
        except Exception as e:  # try the next camera protocol
            errors.append(f"{fn.__name__}: {e}")
    raise RuntimeError("; ".join(errors) + "  (is LAN mode liveview enabled on the printer?)")


def cmd_status(args):
    ip, serial, code = config()
    pr = Printer(ip, serial, code)
    pr.start()
    if not pr.got_report.wait(args.timeout):
        pr.stop()
        sys.exit("No status received. Check IP, serial, access code, and LAN/Developer mode.")
    time.sleep(1.5)  # let the full pushall report land
    pr.stop()
    with pr.lock:
        print(summarize(pr.state))
        if args.raw:
            print(json.dumps(pr.state, indent=2))


def cmd_snapshot(args):
    ip, _, code = config()
    out = args.output or f"snapshot_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    print(snapshot(ip, code, out))


def cmd_watch(args):
    ip, serial, code = config()
    os.makedirs(args.out, exist_ok=True)
    log_path = os.path.join(args.out, "status.jsonl")

    def on_report(delta, state):
        with open(log_path, "a") as f:
            f.write(json.dumps({"t": time.time(), "report": delta}) + "\n")
        with open(os.path.join(args.out, "latest.json"), "w") as f:
            json.dump(state, f, indent=2)
        with open(os.path.join(args.out, "summary.txt"), "w") as f:
            f.write(summarize(state) + "\n")

    pr = Printer(ip, serial, code)
    pr.on_report = on_report
    pr.start()
    print(f"Watching {ip}; writing to {args.out}/ (Ctrl+C to stop)")
    next_snap = 0.0
    next_push = time.time() + args.interval
    try:
        while True:
            now = time.time()
            if args.snap_every and now >= next_snap:
                next_snap = now + args.snap_every
                path = os.path.join(args.out, f"snap_{datetime.now():%Y%m%d_%H%M%S}.jpg")
                try:
                    snapshot(ip, code, path)
                    print("snapshot", path)
                except RuntimeError as e:
                    print("snapshot failed:", e, file=sys.stderr)
            if now >= next_push:
                next_push = now + args.interval
                pr.request_full_status()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        pr.stop()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status"); s.add_argument("--raw", action="store_true"); s.add_argument("--timeout", type=float, default=15)
    s.set_defaults(fn=cmd_status)
    s = sub.add_parser("snapshot"); s.add_argument("-o", "--output"); s.set_defaults(fn=cmd_snapshot)
    s = sub.add_parser("watch")
    s.add_argument("--interval", type=float, default=30, help="seconds between full status requests")
    s.add_argument("--snap-every", type=float, default=60, help="seconds between snapshots (0 = off)")
    s.add_argument("--out", default="print_log")
    s.set_defaults(fn=cmd_watch)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
