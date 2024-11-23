import can
import logging
from can.interfaces.vector.exceptions import VectorInitializationError

# Create an error-specific logger
ErrorLogger = logging.getLogger("ErrorLogger")
ErrorLogger.setLevel(logging.ERROR)

# Create a formatter for the ErrorLogger
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# Create a file handler for the ErrorLogger
error_file_handler = logging.FileHandler("can_receive_errors.log")
error_file_handler.setFormatter(error_formatter)
error_file_handler.setLevel(logging.ERROR)

# Create a console handler for the ErrorLogger
error_console_handler = logging.StreamHandler()
error_console_handler.setFormatter(error_formatter)
error_console_handler.setLevel(logging.ERROR)

# Add both handlers to the ErrorLogger
ErrorLogger.addHandler(error_file_handler)
ErrorLogger.addHandler(error_console_handler)

# Create a general logger for INFO-level logging
logger = logging.getLogger("GeneralLogger")
logger.setLevel(logging.INFO)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# Create a console handler for general logging
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Create a file handler for general logging
file_handler = logging.FileHandler("can_receiver.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Add handlers to the general logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

try:
    # Initialize the CAN bus with the Vector interface
    with can.Bus(interface="vector", channel=0, app_name="fileSenderApp") as bus:
        
        logger.info("CAN bus initialized successfully for receiving messages.")

        try:
            
            logger.info("Waiting to receive a CAN message...")
            # Block until a message is received (timeout=None means wait indefinitely)
            msg = bus.recv(timeout=10)  # Adjust timeout as needed

            if msg is None:
                
                logger.info("Timeout: No CAN message received within the specified time.")
            else:
                print(f"Message received: {msg}")
                logger.info("Message received on %s with arbitration_id=0x%X and data=%s",
                             bus.channel_info, msg.arbitration_id, msg.data)
        except can.CanError as e:
            ErrorLogger.error("Error: CAN error occurred during message reception %s", e)
            

except VectorInitializationError as e:
    ErrorLogger.error("Error: VectorInitializationError: %s, Details: Vector CAN hardware not detected or configured incorrectly. Check connections and drivers.", e)


except ValueError as e:
    ErrorLogger.error("Error: ValueError due to Invalid parameter provided for CAN Bus initialization: %s", e)

except OSError as e:
    ErrorLogger.error("Error: OSError likely due to hardware or system issues: %s", e)


except can.CanError as e:
    ErrorLogger.error("Error: A general CAN-related issue occurred during initialization: %s", e)


except Exception as e:
    ErrorLogger.error("Error: Unexpected exception occurred: %s", e)


finally:
    logger.info("CAN receive operation complete.")
