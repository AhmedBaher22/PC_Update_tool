import isotp
import can
import logging

# Logger setup
ErrorLogger = logging.getLogger("ErrorLogger")
ErrorLogger.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
error_file_handler = logging.FileHandler("isotp_sender_errors.log")
error_file_handler.setFormatter(error_formatter)
error_file_handler.setLevel(logging.ERROR)
error_console_handler = logging.StreamHandler()
error_console_handler.setFormatter(error_formatter)
error_console_handler.setLevel(logging.ERROR)
ErrorLogger.addHandler(error_file_handler)
ErrorLogger.addHandler(error_console_handler)

logger = logging.getLogger("GeneralLogger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler("isotp_sender.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

fd_flag = False
extended_flag = False
channel_number = 0
message_id = 0x33
retries = 3
time_out_in_seconds = 5

def my_rxfn(timeout:float) -> isotp.CanMessage:
    bus=can.Bus(interface="vector", channel=channel_number, app_name="udsWithIsoTp", fd=fd_flag)
    canMsg = bus.recv(timeout)
    return isotp.CanMessage(arbitration_id=canMsg.arbitration_id,
                            data = canMsg.data,
                            extended_id=canMsg.is_extended_id,
                            is_fd=canMsg.is_fd)



def my_txfn(isotp_msg:isotp.CanMessage):
    bus=can.Bus(interface="vector", channel=channel_number, app_name="udsWithIsoTp", fd=fd_flag)
    msg = can.Message(arbitration_id=isotp_msg.arbitration_id, 
                      data=isotp_msg.data, 
                      is_extended_id=isotp_msg.is_extended_id,
                      is_fd=isotp_msg.is_fd)
    bus.send(msg)


try:
    # Initialize CAN bus
    with can.Bus(interface="vector", channel=channel_number, app_name="udsWithIsoTp", fd=fd_flag) as bus:
        print("CAN bus initialized successfully.")
        logger.info("CAN bus initialized successfully.")

        # ISO-TP configuration
        tp_address = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=message_id, rxid=message_id + 1)
        tp_layer = isotp.TransportLayer(txfn=my_txfn, rxfn=my_rxfn, address=tp_address)
        tp_layer.params.tx_padding = 0x00
        tp_layer.params.tx_data_length = 8  # Standard CAN frame data length
        tp_layer.params.stmin = 0  # Minimum separation time (ms)
        tp_layer.params.blocksize = 0  # No block size limit
        # tp_layer.params.tx_arbitration_id = message_ids
        # tp_layer.params.rx_arbitration_id = message_id + 1
        tp_layer.start()
        acknowledgment_received = False
        retries = 3

        msg = bytearray([0, 25, 0, 1, 3, 1, 4, 1,1,1,1,1,11,1,1])
        

        while not acknowledgment_received and retries > 0:
            try:
                tp_layer.send(msg)
                print(f"ISO-TP Message sent: {msg}")
                logger.info("ISO-TP Message sent with arbitration_id=0x%X and data=%s", message_id, message)

                ack = tp_layer.recv(timeout=time_out_in_seconds,block=True)  # Wait for acknowledgment
                if ack:
                    print("Acknowledgment received.")
                    logger.info("Acknowledgment received: %s", ack)
                    acknowledgment_received = True
                else:
                    print("No acknowledgment received. Retrying...")
                    logger.warning("No acknowledgment received. Retrying...")
                    retries -= 1

            except Exception as e:
                ErrorLogger.error("ProtocolError while sending ISO-TP message: %s", e)
                print(f"Error: ProtocolError: {e}")
                retries -= 1

            except can.CanError as e:
                ErrorLogger.error("CanError while sending ISO-TP message: %s", e)
                print(f"Error: CanError: {e}")
                retries -= 1

        if not acknowledgment_received:
            print("Message transmission failed after retries.")
            ErrorLogger.error("Message transmission failed after retries.")

except can.interfaces.vector.exceptions.VectorInitializationError as e:
    ErrorLogger.error("VectorInitializationError: %s", e)
except ValueError as e:
    ErrorLogger.error("Invalid parameter provided for CAN Bus initialization: %s", e)
except OSError as e:
    ErrorLogger.error("OSError likely due to hardware or system issues: %s", e)
except can.CanError as e:
    ErrorLogger.error("A general CAN-related issue occurred: %s", e)
except Exception as e:
    ErrorLogger.error("Unexpected exception occurred: %s", e)
finally:
    logger.info("ISO-TP operation complete.")
