import argparse
import configparser
import os
from logging.config import fileConfig
import logging
import sys
from src.utils.MaskInfoFormatter import MaskInfoFormatter
from src.config.ConfigReader import ConfigReader
from src.manager.TaskManager import TaskManager

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
    Configures the logger and its logging level in memory.
    :param level: the logger logging level
    :param test: flag to indicate if it's a test run
    """
    if test:
        level = "DEBUG"

    logger = logging.getLogger()
    logger.setLevel(level)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(level)

    formatter = MaskInfoFormatter(fmt="%(asctime)s [%(levelname)s]: %(message)s")
    stream_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(stream_handler)

    logging.info(f"Starting Logzio API fetcher in {level} level.")


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
