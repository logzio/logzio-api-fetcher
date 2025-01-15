import os
import yaml
import glob


def validate_config_tokens(secrets_map):
    """
    Validates that the environment variables referenced in token_map exist.
    :param secrets_map: Dictionary of tokens.
    :raises EnvironmentError: If any environment variable is missing.
    """
    for env_var in secrets_map.values():
        if os.getenv(env_var) is None:
            raise EnvironmentError(f"{env_var} environment variable is missing")


def update_config_tokens(file_path, secrets_map):
    """
    Updates the tokens in the given file based on the provided token updates.
    :param file_path: Path to the configuration file.
    :param secrets_map: Dictionary of token updates.
    :return: Path to the temporary configuration file.
    """
    with open(file_path, "r") as conf:
        content = yaml.safe_load(conf)

    for key, env_var in secrets_map.items():
        value = os.getenv(env_var)
        print(f"Updating {key} with {env_var}={value}")
        if value is None:
            raise EnvironmentError(f"{env_var} environment variable is missing")
        keys = key.split('.')
        d = content
        for k in keys[:-1]:
            if k.isdigit():
                k = int(k)
                d = d[k]
            else:
                d = d.setdefault(k, {})
        if keys[-1].isdigit():
            d[int(keys[-1])] = value
        else:
            d[keys[-1]] = value

    path, ext = file_path.rsplit(".", 1)
    temp_test_path = f"{path}_temp.{ext}"

    with open(temp_test_path, "w") as file:
        yaml.dump(content, file)

    return temp_test_path


def delete_temp_files():
    """
    delete the temp config that generated for the test
    """
    curr_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    test_configs_path = f"{curr_path}/apis/testdata/*_temp.yaml"

    for file in glob.glob(test_configs_path):
        os.remove(file)
