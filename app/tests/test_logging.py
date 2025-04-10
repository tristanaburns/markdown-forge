"""
Tests for the logging functionality of the Flask application.
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add app to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logger import get_logger, configure_logger
from utils.route_helpers import track_performance, api_request

class TestLogging(unittest.TestCase):
    """Test cases for logging functionality in the Flask application."""
    
    def setUp(self):
        """Set up test environment."""
        # Configure logger for testing
        self.log_file = "test_logs.json"
        configure_logger(log_level="DEBUG", log_file=self.log_file)
        self.logger = get_logger("test_logger")
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove test log file if it exists
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
    
    def test_basic_logging(self):
        """Test basic logging functionality."""
        test_message = "Test log message"
        self.logger.info(test_message)
        
        # Verify log file contains the message
        with open(self.log_file, 'r') as f:
            logs = [json.loads(line) for line in f.readlines()]
            
        self.assertTrue(any(test_message in log.get('message', '') for log in logs))
    
    def test_context_tracking(self):
        """Test context tracking in logs."""
        self.logger.set_context(page="test_page", user_id="test_user")
        self.logger.info("Log with context")
        self.logger.clear_context()
        
        # Verify log contains context
        with open(self.log_file, 'r') as f:
            logs = [json.loads(line) for line in f.readlines()]
            
        context_log = next((log for log in logs if "Log with context" in log.get('message', '')), None)
        self.assertIsNotNone(context_log)
        self.assertEqual(context_log.get('page'), "test_page")
        self.assertEqual(context_log.get('user_id'), "test_user")
    
    def test_performance_tracking(self):
        """Test performance timer tracking."""
        timer_key = "test_timer"
        self.logger.start_timer(timer_key)
        # Simulate some work
        _ = [i * i for i in range(1000)]
        elapsed = self.logger.stop_timer(timer_key)
        
        # Verify timer recorded time greater than zero
        self.assertGreater(elapsed, 0)
        
        # Log metrics
        self.logger.log_metric("test_metric", elapsed, "ms")
        
        # Verify metric was logged
        with open(self.log_file, 'r') as f:
            logs = [json.loads(line) for line in f.readlines()]
            
        metric_log = next((log for log in logs if "test_metric" in log.get('message', '')), None)
        self.assertIsNotNone(metric_log)
        self.assertIn("ms", metric_log.get('message', ''))
    
    @patch('flask.request')
    @patch('flask.session')
    def test_track_performance_decorator(self, mock_session, mock_request):
        """Test the track_performance decorator."""
        # Mock Flask request and session
        mock_request.path = "/test_route"
        mock_session.get.return_value = "test_user"
        
        # Define a test function with the decorator
        @track_performance(page_name="test_route")
        def test_route():
            return "Test Response"
        
        # Call the decorated function
        result = test_route()
        
        # Verify function returned expected value
        self.assertEqual(result, "Test Response")
        
        # Verify logs were created
        with open(self.log_file, 'r') as f:
            logs = [json.loads(line) for line in f.readlines()]
            
        # Check for route access log
        access_log = next((log for log in logs if "Accessing test_route page" in log.get('message', '')), None)
        self.assertIsNotNone(access_log)
        
        # Check for successful render log
        success_log = next((log for log in logs if "Successfully rendered test_route" in log.get('message', '')), None)
        self.assertIsNotNone(success_log)
    
    @patch('requests.request')
    def test_api_request(self, mock_request):
        """Test the api_request helper function."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response
        
        # Call the api_request function
        response = api_request(url="http://test-api.com/endpoint", method="GET")
        
        # Verify response is correct
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": "test"})
        
        # Verify logs were created
        with open(self.log_file, 'r') as f:
            logs = [json.loads(line) for line in f.readlines()]
            
        # Check for API request log
        request_log = next((log for log in logs if "Making API request" in log.get('message', '')), None)
        self.assertIsNotNone(request_log)
        
        # Check for API response log
        response_log = next((log for log in logs if "API request completed" in log.get('message', '')), None)
        self.assertIsNotNone(response_log)
        
    @patch('requests.request')
    def test_api_request_error(self, mock_request):
        """Test the api_request helper function with an error."""
        # Mock request throwing an exception
        mock_request.side_effect = Exception("API connection error")
        
        # Call the api_request function
        response = api_request(url="http://test-api.com/endpoint", method="GET")
        
        # Verify response is None on error
        self.assertIsNone(response)
        
        # Verify error log was created
        with open(self.log_file, 'r') as f:
            logs = [json.loads(line) for line in f.readlines()]
            
        # Check for API error log
        error_log = next((log for log in logs if "API request failed" in log.get('message', '')), None)
        self.assertIsNotNone(error_log)
        self.assertIn("API connection error", error_log.get('error', ''))

if __name__ == '__main__':
    unittest.main() 