import can
import logging

# Create an error-specific logger
ErrorLogger = logging.getLogger("ErrorLogger")
ErrorLogger.setLevel(logging.ERROR)

# Create a formatter for the ErrorLogger
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# Create a file handler for the ErrorLogger
error_file_handler = logging.FileHandler("can_sender_errors.log")
error_file_handler.setFormatter(error_formatter)
error_file_handler.setLevel(logging.ERROR)

# Create a console handler for the ErrorLogger (prints to terminal)
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
file_handler = logging.FileHandler("can_sender.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Add handlers to the general logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

try:
    # Attempt to initialize the CAN bus with Vector interface
    with can.Bus(interface="vector", channel=0, app_name="fileSenderApp") as bus:
        logger.info("CAN bus initialized successfully using Vector interface.")

        # Create a CAN message
        msg = can.Message(
            arbitration_id=0xC0FFEE,
            data=[0, 25, 0, 1, 3, 1, 4, 1],
            is_extended_id=True
        )

        try:
            # Attempt to send the CAN message
            bus.send(msg)
            print(f"Message sent on {bus.channel_info}")
            logger.info("Message sent successfully on %s with arbitration_id=0x%X and data=%s",
                         bus.channel_info, msg.arbitration_id, msg.data)
                        # Wait for acknowledgment (or the response)
            ack_msg = bus.recv(timeout=1.0)  # Timeout in seconds, adjust as needed
            ack_msg.
            if ack_msg:
                # Log the acknowledgment message if received
                logger.info("Acknowledgment received: %s", ack_msg)
                print("Acknowledgment received")
            else:
                # If no message received in the timeout period
                logger.warning("No acknowledgment received within timeout.")
                print("No acknowledgment received within timeout.")
        except can.CanError as e:
            ErrorLogger.error("Error: CanError while sending a message: %s", e)
            

except can.interfaces.vector.exceptions.VectorInitializationError as e:
    ErrorLogger.error("Error: VectorInitializationError: %s , Details: Vector CAN hardware not detected or configured incorrectly. Check connections and drivers.", e)


except ValueError as e:
    ErrorLogger.error("Error: Invalid parameter provided for CAN Bus initialization: %s", e)
   

except OSError as e:
    ErrorLogger.error("Error: OSError likely due to hardware or system issues: %s", e)


except can.CanError as e:
    ErrorLogger.error("Error: A general CAN-related issue occurred %s", e)


except Exception as e:
    ErrorLogger.error("Error: Unexpected exception occurred: %s", e)


finally:
    logger.info("CAN operation complete.")
