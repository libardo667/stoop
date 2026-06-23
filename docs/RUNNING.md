# Running a Stoop (laptop-era build)

This is the **software-first** build: a Stoop running on a regular computer, reached
over your normal Wi-Fi/LAN. It's how you develop and try the box before it lives on
an ESP32.

> **Note:** all the network wrangling below is a *dev-era* concern. The real
> deployment (major `05`) is an ESP32 broadcasting its **own** open Wi-Fi network —
> a phone just joins it directly and there's no host IP, firewall, or VPN in the
> picture. So if the LAN stuff below is fiddly, know that it disappears on hardware.

## 1. Run it (any OS)

No dependencies, no build step — just Python 3.8+.

```bash
python3 -m src.server
```

Open `http://localhost:8080` on the same machine. That always works.

## 2. Reach it from your phone (same network)

The box listens on `0.0.0.0:8080`, so any device on the same network can reach it —
once it knows the computer's **LAN IP** and nothing is blocking the port.

### Find the computer's LAN IP

- **macOS:** `ipconfig getifaddr en0` (Wi-Fi) or `en1`. Or System Settings → Network.
- **Linux:** `ip -4 addr show scope global | grep inet` — the `192.168.x.x` /
  `10.x.x.x` address.
- **Windows (native):** `ipconfig` → the **IPv4 Address** under your active adapter
  (Wi-Fi or Ethernet), typically `192.168.x.x`.

Then on the phone (on the **same** Wi-Fi), open `http://THAT-IP:8080`.

### If the phone can't connect, in order of likelihood

1. **Firewall.** The host OS is probably blocking inbound `:8080`.
   - **Windows:** allow it (admin PowerShell):
     ```powershell
     New-NetFirewallRule -DisplayName "Stoop 8080" -Direction Inbound `
       -Action Allow -Protocol TCP -LocalPort 8080
     ```
   - **macOS:** System Settings → Network → Firewall → allow incoming for Python,
     or turn the firewall off briefly to test.
   - **Linux:** `sudo ufw allow 8080/tcp` (if `ufw` is active).
2. **A VPN.** Many VPN clients' kill-switches block local/LAN traffic. If you're on
   one (NordVPN, etc.), disconnect it and retry — local devices can't reach you
   through the tunnel.
3. **Different networks.** Phone on cellular, or on a "guest" Wi-Fi that isolates
   clients, won't reach the host. Confirm the phone's IP is the same `192.168.x.x`
   subnet as the computer.

## 3. Special case: Windows + WSL2

If you run the box **inside WSL2**, there's an extra wall: WSL2 sits behind its own
NAT, so `localhost` works from the Windows PC but your phone hitting the Windows LAN
IP finds nothing listening there. Two fixes:

### Recommended — mirrored networking (durable)

Make WSL share the Windows host network. In `C:\Users\<you>\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

Then, from Windows PowerShell:

```powershell
wsl --shutdown
```

Reopen your WSL terminal. Now binding `0.0.0.0:8080` in WSL is reachable at the
Windows LAN IP from your phone. (You may still need the firewall rule from step 2.)
Requires Windows 11 + a recent WSL. Reversible: remove the line and `wsl --shutdown`
again.

### Alternative — port-proxy (no WSL restart)

Forward the host's port into WSL. Get the WSL IP with `wsl hostname -I`, then in
**admin** PowerShell:

```powershell
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8080 `
  connectaddress=<WSL_IP> connectport=8080
New-NetFirewallRule -DisplayName "Stoop 8080" -Direction Inbound -Action Allow `
  -Protocol TCP -LocalPort 8080
```

Works without restarting WSL, but the WSL IP can change on reboot, so the rule needs
re-pointing occasionally. To remove it later:
`netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8080`.
