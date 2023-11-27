import logging
import os


class Logger:
    def __init__(self, log_level="DEBUG", log_location="./", app_name=__name__):
        self.log_level_mapping = {"INFO": logging.INFO, "DEBUG": logging.DEBUG, "ERROR": logging.ERROR,
                                  "WARNING": logging.WARNING}
        self.log_level = log_level
        self.log_location = log_location
        self.app_name = app_name
        self.logger = logging.getLogger(self.app_name)

    def check_log_dir(self):
        if not os.path.isdir(self.log_location):
            mode = 0o744
            os.mkdir(self.log_location, mode)

    @staticmethod
    def close_logger():
        logging.shutdown()

    def start_logger(self):
        self.check_log_dir()
        log_level = self.log_level_mapping[self.log_level]
        self.logger.setLevel(log_level)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            console_handler.setLevel(log_level)
            self.logger.addHandler(console_handler)

        return self.logger
