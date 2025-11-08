# WSL2 Performance Tuning (.wslconfig)

## Overview
`vmmem` is the WSL2 VM manager process. By default, WSL2 can consume up to **80% of your host RAM** and **all available CPU cores**, causing lag when VS Code indexes large repositories or runs intensive Python processes.

## Solution: Create or edit `.wslconfig`
Place this file in your **Windows user profile directory**: `C:\Users\<YourUsername>\.wslconfig`

```ini
[wsl2]
# Limit WSL2 VM memory to 8GB (adjust based on your total RAM; recommended: 25-50% of total)
memory=8GB

# Limit CPU cores (e.g., 4 cores if you have 8+ total; prevents 100% host CPU usage)
processors=4

# Set swap size (default is 25% of memory; reduce if disk I/O is slow)
swap=2GB

# Disable page reporting to reduce memory management overhead
pageReporting=false

# Limit memory growth (WSL2 can release memory back to Windows more aggressively)
vmIdleTimeout=-1

# Optional: disable localhost forwarding if not needed (minor perf gain)
localhostForwarding=true
```

## Applying Changes
1. Save `.wslconfig` in `C:\Users\<YourUsername>\`
2. Shut down WSL2 completely:
   ```powershell
   wsl --shutdown
   ```
3. Restart WSL2 by opening a new WSL terminal or launching VS Code.

## Recommended Values by Host RAM
| Total RAM | memory= | processors= | swap=  |
|-----------|---------|-------------|--------|
| 8 GB      | 4GB     | 2-3         | 1GB    |
| 16 GB     | 6-8GB   | 3-4         | 2GB    |
| 32 GB     | 12-16GB | 4-6         | 4GB    |
| 64 GB     | 20-24GB | 6-8         | 8GB    |

## Additional Tips
- **Restart WSL2 weekly** if uptime is high (memory fragmentation).
- **Close unused VS Code windows** (each instance adds overhead).
- **Use `wsl --list --running`** to see active distributions; shut down extras.
- **Monitor memory**:
  ```bash
  # Inside WSL2:
  free -h
  # On Windows (PowerShell):
  Get-Process vmmem | Select-Object WS
  ```

## Reference
- [Microsoft WSL2 configuration docs](https://learn.microsoft.com/en-us/windows/wsl/wsl-config#wslconfig)
