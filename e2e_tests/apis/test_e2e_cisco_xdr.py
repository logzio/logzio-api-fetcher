import os
import time
import unittest
from unittest.mock import patch, MagicMock
from os.path import abspath, dirname

from e2e_tests.api_e2e_test import ApiE2ETest


class TestCiscoXdrE2E(ApiE2ETest):
    """End-to-end test for Cisco XDR API"""

    def module_specific_setup(self):
        # Add module-specific setup here if needed
        pass

    def module_specific_teardown(self):
        # Add module-specific teardown here if needed
        pass

    @patch('requests.request')
    def test_cisco_xdr_data_in_logz(self, mock_request):
        """Test that Cisco XDR data is properly shipped to Logz.io"""
        
        # Mock OAuth token response
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "mock_access_token_12345",
            "expires_in": 600,
            "token_type": "Bearer"
        }
        
        # Mock observables response
        mock_observables_response = MagicMock()
        mock_observables_response.status_code = 200
        mock_observables_response.json.return_value = {
            "data": [
                {
                    "type": "domain",
                    "value": "test.com",
                    "judgements": {
                        "count": 1,
                        "docs": [
                            {
                                "disposition": 2,
                                "disposition_name": "Malicious",
                                "severity": 50
                            }
                        ]
                    }
                }
            ]
        }
        
        # Configure mock to return different responses for different URLs
        def mock_request_side_effect(method, url, **kwargs):
            if '/iroh/oauth2/token' in url:
                return mock_token_response
            elif '/iroh-enrich/deliberate/observables' in url:
                return mock_observables_response
            else:
                return MagicMock(status_code=404)
        
        mock_request.side_effect = mock_request_side_effect
        
        secrets_map = {
            "apis.0.cisco_client_id": "CISCO_CLIENT_ID",
            "apis.0.client_password": "CISCO_CLIENT_SECRET",
            "logzio.token": "LOGZIO_SHIPPING_TOKEN",
            "apis.0.additional_fields.type": "TEST_TYPE"
        }
        
        curr_path = abspath(dirname(__file__))
        config_path = f"{curr_path}/testdata/cisco_xdr_config.yaml"
        
        # Set environment variables for testing
        os.environ["CISCO_CLIENT_ID"] = "test_client_id"
        os.environ["CISCO_CLIENT_SECRET"] = "test_client_secret"
        os.environ["LOGZIO_SHIPPING_TOKEN"] = "test_shipping_token"
        
        try:
            self.run_main_program(config_path=config_path, secrets_map=secrets_map, test=True)
            time.sleep(10)  # Wait for processing
            
            # Verify that the mock was called correctly
            self.assertTrue(mock_request.called, "Mock request was not called")
            
            # Check that token request was made
            token_calls = [call for call in mock_request.call_args_list 
                          if '/iroh/oauth2/token' in str(call)]
            self.assertTrue(token_calls, "Token request was not made")
            
            # Check that observables request was made
            observables_calls = [call for call in mock_request.call_args_list 
                                if '/iroh-enrich/deliberate/observables' in str(call)]
            self.assertTrue(observables_calls, "Observables request was not made")
            
        finally:
            # Clean up environment variables
            for key in ["CISCO_CLIENT_ID", "CISCO_CLIENT_SECRET", "LOGZIO_SHIPPING_TOKEN"]:
                if key in os.environ:
                    del os.environ[key]

    def test_cisco_xdr_config_validation(self):
        """Test that Cisco XDR configuration is properly validated"""
        from src.apis.cisco_xdr.CiscoXDR import CiscoXdr
        
        # Test valid configuration
        valid_config = {
            'cisco_client_id': 'test_client_id',
            'client_password': 'test_client_secret',
            'data_request': {
                'url': 'https://visibility.amp.cisco.com/iroh/iroh-enrich/deliberate/observables',
                'method': 'POST'
            }
        }
        
        cisco_xdr = CiscoXdr(**valid_config)
        self.assertEqual(cisco_xdr.cisco_client_id, 'test_client_id')
        self.assertEqual(cisco_xdr.client_password, 'test_client_secret')


if __name__ == '__main__':
    unittest.main() 