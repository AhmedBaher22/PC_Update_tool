import can
import logging
import isotp
from udsoncan.connections import PythonIsoTpConnection
from udsoncan import DidCodec
import struct

# Logging setup
ErrorLogger = logging.getLogger("ErrorLogger")
ErrorLogger.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
error_file_handler = logging.FileHandler("uds_server_errors.log")
error_file_handler.setFormatter(error_formatter)
ErrorLogger.addHandler(error_file_handler)

GeneralLogger = logging.getLogger("GeneralLogger")
GeneralLogger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("uds_server.log")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
GeneralLogger.addHandler(console_handler)
GeneralLogger.addHandler(file_handler)

tx_id = 0x34  # Server's transmitter ID
rx_id = 0x33  # Server's receiver ID
fd_flag = False
timeout_seconds = 60

# Custom Codec for VIN (Example of ASCII encoding)
class AsciiCodec(DidCodec):
    def __init__(self, length):
        self.length = length

    def encode(self, val):
        return val.encode('ascii').ljust(self.length, b'\x00')

    def decode(self, payload):
        return payload.decode('ascii').rstrip('\x00')

    def __len__(self):
        return self.length

# Simulated Data Identifiers (DIDs) and their corresponding encoded responses
data_store = {
    b'\xF1\x90': AsciiCodec(15).encode('ABCDE0123456789'),  # Example VIN response using ASCII Codec
}

try:
    # Initialize CAN bus
    with can.Bus(interface="vector", channel=0, app_name="UDS trial", fd=fd_flag) as bus:
        GeneralLogger.info("CAN bus initialized successfully.")

        address = isotp.Address(txid=tx_id, rxid=rx_id)  # ISO-TP addressing
        # Configure ISO-TP Layer
        stack = isotp.CanStack(bus, address=address, params={
            'stmin': 0,  # Minimum separation time (ms)
            'blocksize': 8,  # Block size
            'tx_padding': 0x00,  # Padding for outgoing frames
            'rx_flowcontrol_timeout': 1000,  # Timeout for receiving flow control messages (ms)
            'override_receiver_stmin': 10
        })

        connection = PythonIsoTpConnection(stack)

        GeneralLogger.info("UDS Server is now running.")
        while True:
            try:
                # Receive request
                request = connection.wait_frame(timeout=timeout_seconds)
                if request:
                    GeneralLogger.info("Received UDS request: %s", request.hex())

                    # Handling a Read Data By Identifier (DID) Request
                    if request.startswith(b'\x22'):  # Read Data By Identifier service (0x22)
                        did = request[1:3]  # Extract DID
                        GeneralLogger.info("Received Read DID request for DID: %s", did.hex())

                        if did in data_store:  # Check if DID is supported
                            response = b'\x62' + did + data_store[did]  # Positive Response (0x62)
                            connection.send(response)
                            GeneralLogger.info("Responded to Read DID with: %s", response.hex())
                        else:
                            response = b'\x7F\x22\x31'  # Negative Response: Request Out of Range
                            connection.send(response)
                            GeneralLogger.warning("Unsupported DID requested: %s", did.hex())
                    else:
                        # Negative Response: Service Not Supported
                        response = b'\x7F' + request[:1] + b'\x11'
                        connection.send(response)
                        GeneralLogger.warning("Unsupported service requested: %s", request[:1].hex())
                else:
                    GeneralLogger.info("Timeout: No UDS request received.")

            except Exception as e:
                ErrorLogger.error("Unexpected error during UDS processing: %s", e)

except can.CanError as e:
    ErrorLogger.error("CAN error occurred: %s", e)

except Exception as e:
    ErrorLogger.error("Unexpected exception: %s", e)

finally:
    GeneralLogger.info("UDS Server operation complete.")
