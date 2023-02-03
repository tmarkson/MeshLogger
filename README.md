# MeshLogger
a logging interface for Meshtastic devices

## File explanations
### /bin/MeshLogger.py
#### Dependency
- A USB or network device accessible by user running this script (`dialout` group)
#### usage
- python MeshLogger.py <device>
- python MeshLogger.py COM3
- python MeshLogger.py /dev/ttyACM0
- python MeshLogger.py 192.168.1.5

Run in background with `_run.sh`; persistent.

Alternatively install in cron or another method to run at boot.

#### outputs
'../log/mesh.log' and '../log/mesh_raw.log'
## /log/mesh.log
Human-readable summary of certain log events.
## /log/mesh_raw.log
Store every packet, formatted as it's received. 
