from logging.config import fileConfig
from src.apis_manager import ApisManager


def main() -> None:
    fileConfig('src/logging_config.ini', disable_existing_loggers=False)
    ApisManager().run()


if __name__ == '__main__':
    main()
