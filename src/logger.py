import logging

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,  # Capture all debug messages
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('link_opener.log'),
            logging.StreamHandler()  # Output logs to the terminal
        ]
    ) 