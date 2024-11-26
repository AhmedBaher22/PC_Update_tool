import can
import logging
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection
import isotp  # ISO-TP for transport layer
from udsoncan import configs
import struct
from udsoncan import DidCodec, AsciiCodec
from udsoncan import DataIdentifier
# Define a custom codec as in the example
class MyCustomCodecThatShiftBy4(DidCodec):
    def encode(self, val):
        val = (val << 4) & 0xFFFFFFFF  # Do some stuff
        return struct.pack('<L', val)  # Little endian, 32-bit value

    def decode(self, payload):
        val = struct.unpack('<L', payload)[0]  # Decode the 32-bit value
        return val >> 4  # Reverse the operation

    def __len__(self):
        return 4  # Encoded payload is 4 bytes long.

# Configuration for UDS Client
client_config = dict(configs.default_client_config)

# Define the DID and assign codecs
client_config['data_identifiers'] = {
    'default': '>H',                      # Default codec: 16-bit little-endian
    0x1234: MyCustomCodecThatShiftBy4,    # Custom codec
    0x1235: MyCustomCodecThatShiftBy4(),  # Another instance of custom codec
    0xF190: AsciiCodec(15)                # ASCII codec for 15-character string
}

# Create an error-specific logger
ErrorLogger = logging.getLogger("ErrorLogger")
ErrorLogger.setLevel(logging.ERROR)

# Error logger handlers
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
error_file_handler = logging.FileHandler("can_sender_errors.log")
error_file_handler.setFormatter(error_formatter)
error_console_handler = logging.StreamHandler()
error_console_handler.setFormatter(error_formatter)
ErrorLogger.addHandler(error_file_handler)
ErrorLogger.addHandler(error_console_handler)

# Create a general logger for INFO-level logging
logger = logging.getLogger("GeneralLogger")
logger.setLevel(logging.INFO)

# General logger handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler("can_sender.log")
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

fd_flag = False
extended_flag = False
channel_number = 0
tx_id = 0x33  # Transmitter ID
rx_id = 0x34  # Receiver ID
time_out_in_seconds = 5

try:
    # Initialize CAN bus
    with can.Bus(interface="vector", channel=channel_number, app_name="UDS trial", fd=fd_flag) as bus:
        logger.info("CAN bus initialized successfully for UDS Client.")
        
        address = isotp.Address(txid=tx_id, rxid=rx_id)  # ISO-TP addressing
        # Configure ISO-TP Layer
        stack = isotp.CanStack(bus, address=address, params={
            'stmin': 0,  # Minimum separation time (ms)
            'blocksize': 8,  # Block size
            'tx_padding': 0x00,  # Padding for outgoing frames
            'rx_flowcontrol_timeout': 1000,  # Timeout for receiving flow control messages (ms)
            'override_receiver_stmin': 10
        })

        uds_connection = PythonIsoTpConnection(stack)

        # Pass the config when initializing the UDS Client
        try:
            with Client(uds_connection, config=client_config) as client:
                logger.info("UDS Client initialized successfully.")
                
                try:
                    # Sending a Read Data by Identifier (DID) request
                    logger.info("Sending UDS request: Read Data by Identifier (DID).")
                    response = client.read_data_by_identifier([DataIdentifier.VIN])
                    vin = response.service_data.values[DataIdentifier.VIN]  # Access the value of the DID
                    print(vin)  # Should output VIN
                    logger.info(f"VIN received: {vin}")
                except Exception as e:
                    ErrorLogger.error("UDS request failed: %s", e)
                    print(f"UDS request failed: {e}")
        except Exception as e:
            ErrorLogger.error("Error initializing UDS Client: %s", e)
except can.CanError as e:
    ErrorLogger.error("CAN error occurred: %s", e)

except Exception as e:
    ErrorLogger.error("Unexpected exception: %s", e)

finally:
    logger.info("CAN UDS Client operation complete.")
