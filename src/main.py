from logging.config import fileConfig
from api_handler import ApiHandler


def main():
    fileConfig('logging_config.ini', disable_existing_loggers=False)
    ApiHandler().run()


if __name__ == '__main__':
    main()
