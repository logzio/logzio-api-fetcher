import logging

from pydantic import ValidationError
import yaml

# Needed for creating the input and output instances
from src.apis.general.Api import ApiFetcher
from src.apis.oauth.OAuth import OAuthApi
from src.apis.azure.AzureGraph import AzureGraph
from src.apis.azure.AzureMailReports import AzureMailReports
from src.apis.cloudflare.Cloudflare import Cloudflare
from src.apis.onepassword.OnePassword import OnePassword
from src.output.LogzioShipper import LogzioShipper
from src.apis.dockerhub.Dockerhub import DockerHub
from src.apis.google.GoogleWorkspace import GoogleWorkspace
from src.apis.google.GoogleWorkspaceActivity import GoogleWorkspaceActivity

INPUT_API_FIELD = "apis"
OUTPUT_LOGZIO_FIELD = "logzio"
API_TYPES_TO_CLASS_NAME_MAPPING = {
    "general": "ApiFetcher",
    "oauth": "OAuthApi",
    "azure_general": "AzureApi",
    "azure_graph": "AzureGraph",
    "azure_mail_reports": "AzureMailReports",
    "cloudflare": "Cloudflare",
    "1password": "OnePassword",
    "dockerhub": "DockerHub",
    "google_workspace": "GoogleWorkspace",
    "google_activity": "GoogleWorkspaceActivity",
}

logger = logging.getLogger(__name__)


class ConfigReader:
    """
    Class that reads a Yaml config and generates instances based on it
    """
    def __init__(self, conf_file):
        """
        Receives a path to a config file, reads it and generates other classes instances based on it.
        :param conf_file: path to the config file
        """
        self.config = self._read_config(conf_file)
        self.api_instances, self.logzio_shipper = self.generate_instances()

    @staticmethod
    def _read_config(conf_file):
        """
        Opens the given Yaml configuration file.
        :param conf_file: yaml config file path
        :return: content of the given file
        """
        try:
            logger.debug(f"Reading config file {conf_file}")
            with open(conf_file, "r") as conf:
                return yaml.safe_load(conf)
        except FileNotFoundError:
            logger.error(f"Did not find file {conf_file}.")
        except PermissionError:
            logger.error(f"Missing read permission for file {conf_file}.")
        except Exception as e:
            logger.error(f"Failed to read config from path {conf_file} due to error {e}.")
        return None

    def generate_instances(self):
        """
        Uses 'pydantic' to validate the given APIs config and generates API fetcher per valid config.
        :return: API fetcher (ApiFetcher) instances
        """
        api_instances = []
        logzio_shipper_instance = None
        shipper_cls = globals().get("LogzioShipper")
        if not self.config:
            return api_instances, logzio_shipper_instance
        apis = self.config.get(INPUT_API_FIELD)
        logzio_conf = self.config.get(OUTPUT_LOGZIO_FIELD)

        if not apis:
            logger.error(f"No inputs defined. Please make sure your API input is configured under '{INPUT_API_FIELD}'")
            return api_instances, logzio_shipper_instance

        # Generate API fetchers
        for api_conf in apis:
            try:
                api_type_cls_name = API_TYPES_TO_CLASS_NAME_MAPPING.get(api_conf.get("type"))
                api_cls = globals().get(api_type_cls_name)
                api_instance = api_cls(**api_conf)
                api_instances.append(api_instance)
                logger.debug(f"Created {api_instance.name}.")
            except (AttributeError, ValidationError, TypeError) as e:
                logger.error(f"Failed to create API fetcher for config {api_conf} due to error: {e}")

        # Generate Logzio shipper
        if not logzio_conf:
            logger.warning(f"No Logzio shipper output defined. Please make sure your Logzio config is configured under "
                           f"{OUTPUT_LOGZIO_FIELD}")
        else:
            try:
                logzio_shipper_instance = shipper_cls(**logzio_conf)
                logger.debug("Created logzio shipper.")
            except (ValidationError, TypeError) as e:
                logger.error(f"Failed to create Logzio shipper for config {logzio_conf} due to error: {e}")

        return api_instances, logzio_shipper_instance
