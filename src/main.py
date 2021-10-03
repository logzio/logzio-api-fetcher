from logging.config import fileConfig
from .apis_manager import ApisManager


def main():
    fileConfig('logging_config.ini', disable_existing_loggers=False)
    ApisManager().run()


if __name__ == '__main__':
    main()
