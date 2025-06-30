import unittest
import base64
from unittest.mock import patch, MagicMock
from src.apis.cisco_xdr.CiscoXDR import CiscoXdr
from src.apis.general.Api import ReqMethod


class TestCiscoXdr(unittest.TestCase):
    """Test cases for Cisco XDR API driver"""

    def test_cisco_xdr_initialization(self):
        """Test basic initialization of Cisco XDR API"""
        config = {
            'cisco_client_id': 'test_client_id',
            'client_password': 'test_client_password',
            'data_request': {
                'url': 'https://visibility.amp.cisco.com/iroh/iroh-enrich/deliberate/observables',
                'method': 'POST'
            }
        }
        
        cisco_xdr = CiscoXdr(**config)
        
        self.assertEqual(cisco_xdr.cisco_client_id, 'test_client_id')
        self.assertEqual(cisco_xdr.client_password, 'test_client_password')

    def test_token_request_configuration(self):
        """Test that token request is properly configured with Basic Auth"""
        config = {
            'cisco_client_id': 'test_client_id',
            'client_password': 'test_client_password',
            'data_request': {
                'url': 'https://visibility.amp.cisco.com/iroh/iroh-enrich/deliberate/observables',
                'method': 'POST'
            }
        }
        
        cisco_xdr = CiscoXdr(**config)
        
        # Check token request configuration
        self.assertEqual(cisco_xdr.token_request.url, 'https://visibility.amp.cisco.com/iroh/oauth2/token')
        self.assertEqual(cisco_xdr.token_request.method, ReqMethod.POST)
        self.assertEqual(cisco_xdr.token_request.headers['Content-Type'], 'application/x-www-form-urlencoded')
        self.assertEqual(cisco_xdr.token_request.headers['Accept'], 'application/json')
        
        # Check Basic Auth header
        expected_credentials = base64.b64encode('test_client_id:test_client_password'.encode()).decode()
        self.assertEqual(cisco_xdr.token_request.headers['Authorization'], f'Basic {expected_credentials}')
        
        # Check body
        self.assertEqual(cisco_xdr.token_request.body, 'grant_type=client_credentials')

    def test_data_request_configuration(self):
        """Test that data request is properly configured"""
        config = {
            'cisco_client_id': 'test_client_id',
            'client_password': 'test_client_password',
            'data_request': {
                'url': 'https://visibility.amp.cisco.com/iroh/iroh-enrich/deliberate/observables',
                'method': 'POST',
                'body': [{'type': 'domain', 'value': 'test.com'}]
            }
        }
        
        cisco_xdr = CiscoXdr(**config)
        
        # Check data request configuration
        self.assertEqual(cisco_xdr.data_request.url, 'https://visibility.amp.cisco.com/iroh/iroh-enrich/deliberate/observables')
        self.assertEqual(cisco_xdr.data_request.method, ReqMethod.POST)
        self.assertEqual(cisco_xdr.data_request.headers['Content-Type'], 'application/json')
        self.assertEqual(cisco_xdr.data_request.headers['Accept'], 'application/json')

    def test_data_request_with_custom_headers(self):
        """Test that custom headers in data_request are preserved"""
        config = {
            'cisco_client_id': 'test_client_id',
            'client_password': 'test_client_password',
            'data_request': {
                'url': 'https://visibility.amp.cisco.com/iroh/iroh-enrich/deliberate/observables',
                'method': 'POST',
                'headers': {
                    'Custom-Header': 'custom_value'
                }
            }
        }
        
        cisco_xdr = CiscoXdr(**config)
        
        # Check that both default and custom headers are present
        self.assertEqual(cisco_xdr.data_request.headers['Content-Type'], 'application/json')
        self.assertEqual(cisco_xdr.data_request.headers['Accept'], 'application/json')
        self.assertEqual(cisco_xdr.data_request.headers['Custom-Header'], 'custom_value')


if __name__ == '__main__':
    unittest.main() 