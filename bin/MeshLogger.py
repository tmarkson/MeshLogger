### MeshLogger.py
# Author: tcm <spam@noclip.sh>
#
# Description: Connect to Meshtastic device via Serial or TCP and log incoming packets.
#              Output 2 log files: 'mesh.log' and 'mesh_raw.log'
#
# Usage examples:
#   python MeshLogger.py <device>
#   python MeshLogger.py COM3
#   python MeshLogger.py /dev/ttyACM0
#   python MeshLogger.py 192.168.1.5

import sys, time, logging, json, socket

from pubsub import pub

import meshtastic
import meshtastic.serial_interface
import meshtastic.tcp_interface

if len(sys.argv) < 2:
    print(f"usage:\n  {sys.argv[0]} 192.168.x.y\n  {sys.argv[0]} COMn\n  {sys.argv[0]} /dev/ttyUSBn")
    sys.exit(1)

# set root log level
logging.basicConfig( level=logging.INFO )

# setup log file hanglers
def doSetupLoggerFile(name, log_file, level=logging.info):
    if name == 'mesh_raw_log':
        formatter = logging.Formatter('\n%(asctime)s - %(name)s - %(levelname)s --\n%(message)s')
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -- %(message)s')

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    
    if name == 'mesh_log':
        logger.propagate = True
    else:
        logger.propagate = False
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def doSetupLoggerStdout(name, level=logging.info):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -- %(message)s')

    handler = logging.StreamHandler()        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# make log files
meshLog = doSetupLoggerFile('mesh_log', '../log/mesh.log', logging.INFO)
meshRawLog = doSetupLoggerFile('mesh_raw_log', '../log/mesh_raw.log', logging.DEBUG)





class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("UTF8")
        return json.JSONEncoder.default(self, obj)






# arg:packet -- the entire message received
# arg:interface -- local class variable; data is updated from a relevant message
def onReceive(packet, interface):
    """called when a packet arrives"""
    
    # live message data
    packet_Decoded = packet['decoded']
    meshRawLog.debug( packet_Decoded )

    if packet_Decoded['portnum'] == 'TEXT_MESSAGE_APP':
        fromUser = packet['fromId']
        toUser = packet['toId']
        message = packet_Decoded['payload'].decode('UTF8')
        meshLog.info( f'Node {fromUser} sent message to {toUser}: {message}' )
    
    elif packet_Decoded['portnum'] == 'NODEINFO_APP':
        user = packet['fromId']
        nameLong = packet_Decoded['user']['longName']
        nameShort = packet_Decoded['user']['shortName']
        hardwareModel = packet_Decoded['user']['hwModel']
        meshLog.info( f'Node {user} is named {nameLong} ({nameShort}) of type {hardwareModel}' )
    
    elif packet_Decoded['portnum'] == 'TELEMETRY_APP':
        packet_Telemetry = packet_Decoded['telemetry']
        if 'deviceMetrics' in packet_Telemetry:
            packet_DeviceMetrics = packet_Telemetry['deviceMetrics']
            if 'voltage' in packet_DeviceMetrics:
                user = packet['fromId']
                voltage = packet_DeviceMetrics['voltage']
                meshLog.info( f'Node {user} reports {voltage}V' )
        else:
            meshLog.info( 'Incomplete packet from TELEMETRY_APP. Might have env metrics.' )
    
    elif packet_Decoded['portnum'] == 'POSITION_APP':
        packet_Position = packet_Decoded['position']
        if all(k in packet_Position for k in ("latitudeI","longitudeI","altitude")) and any(k in packet_Position for k in ("rx_time","time")):
            user = packet['fromId']
            if 'time' in packet_Position: time = packet_Position['time']
            else: time = packet_Position['rx_time']
            lat = packet_Position['latitudeI'] / 1e7
            lon = packet_Position['longitudeI'] / 1e7
            alt = packet_Position['altitude']
            meshLog.info( f'Node {user} reported position: {time},{lat},{lon},{alt}m (epoch,lat,lon,alt)' )
            del time,lon,lat,alt,user
        else:
            meshLog.info( 'Incomplete packet from POSITION_APP; missing keys in packet.' )

    else:
        packetType = packet_Decoded['portnum']
        meshLog.info(f'Received other packet from {packetType}.')

def onConnection(interface, topic=pub.AUTO_TOPIC):
    """called when we (re)connect to the radio"""
    # defaults to broadcast, specify a destination ID if you wish
    meshLog.info(f'Connected.')

pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")

attempts = 0
while True:
    try:
        meshLog.info( f"Connect attempt #{attempts} to {sys.argv[1]}" )
        
        if 'com' in sys.argv[1].lower() or 'tty' in sys.argv[1].lower():
            iface = meshtastic.serial_interface.SerialInterface(devPath=sys.argv[1])
        else:
            iface = meshtastic.tcp_interface.TCPInterface(hostname=sys.argv[1])
        
        attempts += 1
        while True: time.sleep(1000)
        
        iface.close()
    except(OSError) as ex:
        meshLog.info(f"OSError handled, continuing ...\n{ex}\n<3 ted")
        continue
    except(Exception) as ex:
        meshLog.info(f"Error: Could not connect to {sys.argv[1]}\n{ex}\nContinuing... <3 ted")
        continue

