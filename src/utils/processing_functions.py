import json
import logging
import re

# EXPECTED_
VARS_PATTERN = re.compile(r"\{res\.(.*?)\}")
EXPECTED_ARRAY_PREFIX = "["
EXPECTED_ARRAY_SUFFIX = "]"

logger = logging.getLogger(__name__)


def extract_vars(item):
    """
    Receives String item, extract variables names from it and returns array with all the variable names.
    Variable is recognized based on VARS_PATTERN.
    :param item: String value
    :return: array with all the variable names.
    """
    if not item:
        return []
    if not isinstance(item, str):
        item = json.dumps(item)
    return re.findall(VARS_PATTERN, item)


def _support_math_operations(last_nested_key):
    """
    If the given key contains + or - operation, split operation from the key name, and return:
    - the key name without the operation
    - the integer value that needs to be added to the final value.
    :param last_nested_key: key name that may contain a mathematical operation.
    :return: the key name and mathematical operation to perform on the final value.
    """
    if "+" in last_nested_key:
        last_nested_key_without_op, math_operation = last_nested_key.split("+")
        return last_nested_key_without_op, int(math_operation)
    elif "-" in last_nested_key:
        last_nested_key_without_op, math_operation = last_nested_key.split("-")
        return last_nested_key_without_op, -int(math_operation)
    return last_nested_key, None


def _get_key_from_nested_array(next_item, key):
    """
    Expects to get array next_item and a key index.
    Extracts the index from the given next item and returns it.
    If encounters an error, returns None.
    :param next_item: an array
    :param key: the index to get from the array
    :return: the value of item in given index of the next given item.
    """
    key = key[len(EXPECTED_ARRAY_PREFIX):-len(EXPECTED_ARRAY_SUFFIX)]
    try:
        next_item = next_item[int(key)]
    except (IndexError, ValueError):
        logger.warning(f"Failed to find the next key: '{key}' nested in {next_item}")
        logger.warning("Failed to find the next key: '%s' nested in %s", key, next_item)
        next_item = None
    return next_item


def _get_key_from_nested(next_item, key):
    """
    Expects to get a dictionary next_item and a key name.
    Extracts the key value from the dictionary and returns it.
    If encounters an error, returns None.
    :param next_item: dictionary with values
    :param key: key in the dictionary
    :return: the key value or None if it doesn't exist in the dict.
    """
    _SENTINEL = object()  # To allow differentiating between case of field not exists VS field value is None
    original = next_item  # Keeping it for logging purpose

    try:
        next_item = next_item.get(key, _SENTINEL)

        # The key does not exist in the dictionary
        if next_item is _SENTINEL:
            logger.warning(f"Key '{key}' does not exists in: {original}")
            next_item = None

    except AttributeError:
        # Check if nested value is in a flattened object and extract it
        try:
            next_item = _get_key_from_nested(json.loads(next_item), key)
        except json.decoder.JSONDecodeError:
            logger.debug(f"Failed to find '{key}' in response due to error.")
            next_item = None
    return next_item


def get_nested_value(values_dic, nested_keys):
    """
    Receives an array of keys who are nested, in their nesting order.
    Examples: obj = {'key1': {'key2': 123}} >> nested_keys = ['key1', 'key2']
              obj =  {'key1': [{'key2': 123}]} >> nested_keys = ['key1', '[0]', 'key2']
    And returns the final value from the values_dic.
    If doesn't exist, returns None
    :param values_dic: Dictionary with keys (such as from nested_keys) and their values
    :param nested_keys: Array of key names that are nested, in order of their nesting
    :return: value of the given nested keys
    """
    next_item = values_dic
    last_item_index = len(nested_keys) - 1

    # Support + and - math operations
    last_nested_key = nested_keys[last_item_index]
    nested_keys[last_item_index], math_operation = _support_math_operations(last_nested_key)

    for key in nested_keys:
        # Support array keys
        if key.startswith(EXPECTED_ARRAY_PREFIX) and key.endswith(EXPECTED_ARRAY_SUFFIX):
            next_item = _get_key_from_nested_array(next_item, key)

        # Not an array key
        else:
            key = key.replace("~~", ".")
            next_item = _get_key_from_nested(next_item, key)

        # We either got an exception, the key does not exist or next_item == None >> break from the loop
        if not next_item:
            break

    if next_item and math_operation:
        next_item += math_operation
    return next_item


def replace_dots(string):
    """
    Replaces all the dots of a given string with ~~
    :param string: some String value
    :return: the given string value with ~~ instead of dots.
    """
    return string.replace("\\.", "~~")


def break_key_name(key):
    """
    Receives a key name in format:
    - 'key', 'key.nested', 'key.[0].nested' ...
    and returns an array with the nested keys in order.
    :param key: nested key name
    :return: array of the nested fields in the key in order.
    """
    return replace_dots(key).split(".")


def substitute_vars(item, vars_arr, values_dic):
    """
    Receives String item and replaces the variables from vars_arr in it with their values from the values_dic.
    :param item: String item with variables in it
    :param vars_arr: array with the variables to replace in the item
    :param values_dic: dictionary with the keys and values.
    :return: the item with values instead of variables.
    """
    new_item = item
    for var in vars_arr:
        # Support dots in key names and nested objects
        var_fields = break_key_name(var)

        # Find the key in the response and put value in next_item
        value = get_nested_value(values_dic, var_fields)
        if value:
            new_item = new_item.replace("{res.%s}" % var, str(value))
        else:
            raise ValueError(f"The response didn't contain {var} hence it won't be replaced in {item}.")
    return new_item
