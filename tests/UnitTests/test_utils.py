import unittest

from src.utils.processing_functions import extract_vars, get_nested_value, replace_dots, break_key_name, substitute_vars


class TestUtilsFunctions(unittest.TestCase):
    """
    Test utils functions
    """

    def test_extract_vars(self):
        # Test cases
        valid_var_use = "correct vars {res.field} usage {res.[0]}/{res.test\\.f2}"
        invalid_var_use = "wrong vars {field} usage {[0]}/{test\\.f2}"

        # Assert they behave as expected
        self.assertEqual(extract_vars(valid_var_use), ["field", "[0]", "test\\.f2"])
        self.assertEqual(extract_vars(invalid_var_use), [])
        self.assertEqual(extract_vars(123), [])
        self.assertEqual(extract_vars(["a", "b", "c"]), [])
        self.assertEqual(extract_vars({"field": "{res.hello}"}), ["hello"])

    def test_get_nested_value(self):
        # Test case
        test_dic = {
            "field": "hello",
            "arr": [1, 2, 3],
            "obj_arr": [{"f1": 123}, {"f1": 456, "f2": "abc"}],
            "obj": {
                "nested": "random value"
            },
            "none": None,
            "dot.in.name": "the value"
        }

        # Assert it behaves as expected
        self.assertEqual(get_nested_value(test_dic, ["field"]), "hello")
        self.assertEqual(get_nested_value(test_dic, ["arr", "[2]"]), 3)
        self.assertEqual(get_nested_value(test_dic, ["obj_arr", "[0]", "f1"]), 123)
        self.assertEqual(get_nested_value(test_dic, ["obj", "nested"]), "random value")
        self.assertEqual(get_nested_value(test_dic, ["none"]), None)
        self.assertEqual(get_nested_value(test_dic, ["dot~~in~~name"]), "the value")

        with self.assertLogs("src.utils.processing_functions", level='WARN') as log:
            result = get_nested_value(test_dic, ["arr", "[3]"])
            result2 = get_nested_value(test_dic, ["not_existing_field"])
        self.assertIn("WARNING:src.utils.processing_functions:Failed to find the next key: '3' nested in [1, 2, 3]", log.output)
        self.assertIn("WARNING:src.utils.processing_functions:Key 'not_existing_field' does not exists in: {'field': 'hello', 'arr': [1, 2, 3], 'obj_arr': [{'f1': 123}, {'f1': 456, 'f2': 'abc'}], 'obj': {'nested': 'random value'}, 'none': None, 'dot.in.name': 'the value'}", log.output)
        self.assertEqual(result, None)
        self.assertEqual(result2, None)

    def test_replace_dots(self):
        # Test cases
        should_replace = "field\\.name"
        do_not_replace = "field.name"
        joint_dots = "field.name\\.replace.test"

        # Assert they behave as expected
        self.assertEqual(replace_dots(should_replace), "field~~name")
        self.assertEqual(replace_dots(do_not_replace), "field.name")
        self.assertEqual(replace_dots(joint_dots), "field.name~~replace.test")

    def test_break_key_name(self):
        # Test cases
        do_not_break = "field\\.name"
        do_break = "field.name"

        # Assert they behave as expected
        self.assertEqual(break_key_name(do_not_break), ["field~~name"])
        self.assertEqual(break_key_name(do_break), ["field", "name"])

    def test_substitute_vars(self):
        # Test cases
        test_dic = {
            "field": "hello",
            "arr": [1, 2, 3],
            "obj_arr": [{"f1": 123}, {"f1": 456, "f2": "abc"}],
            "obj": {
                "nested": "random value"
            },
            "none": None,
            "dot.in.name": "the value"
        }

        valid_vars = "{res.field}! just a {res.obj.nested} {res.arr.[1]}"
        no_vars = "just a string with no vars"
        not_valid_vars = "{field}! just testing {res.obj_arr[2].f1}"
        empty_val_throw_error = "can also handle {res.none}!"

        # Assert they behave as expected
        self.assertEqual(substitute_vars(valid_vars, extract_vars(valid_vars), test_dic),
                         "hello! just a random value 2")

        with self.assertRaises(ValueError):
            substitute_vars(not_valid_vars, extract_vars(not_valid_vars), test_dic)
            substitute_vars(empty_val_throw_error, extract_vars(empty_val_throw_error), test_dic)

        self.assertEqual(substitute_vars(no_vars, extract_vars(no_vars), test_dic), no_vars)
