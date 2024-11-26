import logging
import isotp
import can
from can.interfaces.vector.exceptions import VectorInitializationError

# Error Logger setup
ErrorLogger = logging.getLogger("ErrorLogger")
ErrorLogger.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
error_file_handler = logging.FileHandler("isotp_receiver_errors.log")
error_file_handler.setFormatter(error_formatter)
error_console_handler = logging.StreamHandler()
error_console_handler.setFormatter(error_formatter)
ErrorLogger.addHandler(error_file_handler)
ErrorLogger.addHandler(error_console_handler)

# General Logger setup
logger = logging.getLogger("GeneralLogger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
file_handler = logging.FileHandler("isotp_receiver.log")
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

fd_flag = False
extended_flag = False
channel_number = 0
message_id = 0x33  # Same as transmitter's txid
timeout_in_seconds = 10  # Timeout for receiving acknowledgment
def my_rxfn(timeout:float) -> isotp.CanMessage:
    bus=can.Bus(interface="vector", channel=channel_number, app_name="udsWithIsoTp", fd=fd_flag)
    canMsg = bus.recv(timeout)
    return isotp.CanMessage(arbitration_id=canMsg.arbitration_id,
                            data = canMsg.data,
                            extended_id=canMsg.is_extended_id,
                            is_fd=canMsg.is_fd)



def my_txfn(isotp_msg:isotp.CanMessage):
    print("I am here")
    bus=can.Bus(interface="vector", channel=channel_number, app_name="udsWithIsoTp", fd=fd_flag)
    msg = can.Message(arbitration_id=isotp_msg.arbitration_id, 
                      data=isotp_msg.data, 
                      is_extended_id=isotp_msg.is_extended_id,
                      is_fd=isotp_msg.is_fd)
    bus.send(msg)

try:
    # Initialize CAN bus
    with can.Bus(interface="vector", channel=channel_number, app_name="udsWithIsoTp", fd=fd_flag) as bus:
        logger.info("CAN bus initialized successfully for ISO-TP.")

        # ISO-TP configuration
        tp_address = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=message_id + 1, rxid=message_id)
        tp_layer = isotp.TransportLayer(txfn=my_txfn, rxfn=my_rxfn, address=tp_address)
        tp_layer.params.tx_padding = 0x00  # Same as transmitter
        tp_layer.params.tx_data_length = 8  # Standard CAN frame data length
        tp_layer.params.stmin = 0  # Minimum separation time (ms)
        tp_layer.params.blocksize = 0  # No block size limit

        tp_layer.start()  # Start the transport layer

        while True:
            logger.info("Waiting to receive an ISO-TP message...")
            try:
                # Receive a message from the sender
                message = tp_layer.recv(block=True,timeout=60)
                if message:
                    logger.info("Received ISO-TP message: Data=%s", message.hex())
                    print(f"Message received: {message.hex()}")
                    ack_msg = bytearray([0, 25, 0, 1, 3, 1, 4, 1,1,1,1,1,11,1,1])
                    # Send acknowledgment back to the sender
                    # acknowledgment_message = b'\x01'  # Acknowledgment payload
                    tp_layer.send(ack_msg)
                    logger.info("Acknowledgment sent successfully.")
                else:
                    logger.info("Timeout: No message received.")
                    print("Timeout: No message received.")

            except isotp.ProtocolError as e:
                ErrorLogger.error("ProtocolError while receiving ISO-TP message: %s", e)

            except can.CanError as e:
                ErrorLogger.error("CAN error occurred while receiving a message: %s", e)

except VectorInitializationError as e:
    ErrorLogger.error(
        "VectorInitializationError: Ensure Vector CAN hardware is connected and configured correctly: %s", e
    )
except ValueError as e:
    ErrorLogger.error("Invalid parameter provided for CAN Bus initialization: %s", e)
except OSError as e:
    ErrorLogger.error("OSError likely due to hardware or system issues: %s", e)
except can.CanError as e:
    ErrorLogger.error("General CAN-related issue occurred during initialization: %s", e)
except Exception as e:
    ErrorLogger.error("Unexpected exception occurred: %s", e)
finally:
    logger.info("ISO-TP receive operation complete.")
    if 'tp_layer' in locals():
        tp_layer.stop()
