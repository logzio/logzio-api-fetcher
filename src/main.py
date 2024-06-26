import argparse
import configparser
import logging
from logging.config import fileConfig

from src.config.ConfigReader import ConfigReader
from src.manager.TaskManager import TaskManager

LOGGER_CONFIG_PATH = "./src/utils/logging_config.ini"
FETCHER_CONFIG_PATH = "./src/shared/config.yaml"


def __get_args():
    """
    Gets the level arguments from the run command.
    :return: arguments
    """
    parser = argparse.ArgumentParser(description='Logzio API Fetcher')
    parser.add_argument('--level', type=str, required=False, default='INFO', choices=['INFO', 'WARN', 'ERROR', 'DEBUG'],
                        help='Logging level (One of INFO, WARN, ERROR, DEBUG)')
    return parser.parse_args()


def _setup_logger(level, test):
    """
    Configures the logger and it's logging level.
    :param level: the logger logging level
    """
    # If test, always set to debug
    if test:
        level = "DEBUG"

    # Update the level in the config file
    if level != "INFO":
        logging_conf = configparser.RawConfigParser()
        logging_conf.read(LOGGER_CONFIG_PATH)

        logging_conf['logger_root']['level'] = level
        logging_conf['handler_stream_handler']['level'] = level

        with open(LOGGER_CONFIG_PATH, 'w') as configfile:
            logging_conf.write(configfile)

    # Load the config to the logger
    fileConfig(LOGGER_CONFIG_PATH, disable_existing_loggers=False)
    logging.info(f'Starting Logzio API fetcher in {level} level.')


def main(conf_path=FETCHER_CONFIG_PATH, test=False):
    """
    Get args >> Configure logger >> Read config file >> Start API fetching and shipping task based on config
    """
    args = __get_args()
    _setup_logger(args.level, test)

    conf = ConfigReader(conf_path)

    if conf.api_instances:
        TaskManager(apis=conf.api_instances, logzio_shipper=conf.logzio_shipper).run()


if __name__ == '__main__':
    main()
