import argparse
import configparser
import logging
from logging.config import fileConfig

from src.config.ConfigReader import ConfigReader
from src.manager.TaskManager import TaskManager

logger_config_path = "./src/utils/logging_config.ini"
fetcher_config_path = "./src/shared/config.yaml"


def __get_args():
    """
    Gets config path and level arguments from the run command.
    :return: arguments
    """
    parser = argparse.ArgumentParser(description='Logzio API Fetcher')
    parser.add_argument('--level', type=str, required=False, default='INFO', choices=['INFO', 'WARN', 'ERROR', 'DEBUG'],
                        help='Logging level (One of INFO, WARN, ERROR, DEBUG)')
    return parser.parse_args()


def _setup_logger(level):
    """
    Configures the logger and it's logging level.
    :param level: the logger logging level
    """
    # Update the level in the config file
    logging_conf = configparser.RawConfigParser()
    logging_conf.read(logger_config_path)

    logging_conf['logger_root']['level'] = level
    logging_conf['handler_stream_handler']['level'] = level

    with open(logger_config_path, 'w') as configfile:
        logging_conf.write(configfile)

    # Load the config to the logger
    fileConfig(logger_config_path, disable_existing_loggers=False)
    logging.info(f'Starting Logzio API fetcher in {level} level.')


def main():
    """
    Get args >> Configure logger >> Read config file >> Start API fetching and shipping task based on config
    """
    args = __get_args()
    _setup_logger(args.level)

    conf = ConfigReader(fetcher_config_path)

    if conf.api_instances:
        TaskManager(apis=conf.api_instances, logzio_shipper=conf.logzio_shipper).run()


if __name__ == '__main__':
    main()
