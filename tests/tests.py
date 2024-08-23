import unittest
from app import app  # Import the Flask app instance from app.py

class APITestCase(unittest.TestCase):

    def setUp(self):
        """Set up a test client before each test."""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_add_user_post_valid_unauthorised(self):
        """Test the /api/add_user endpoint with a valid POST request."""
        # Define a valid payload for adding a user
        valid_data = {
            'external_key': '643463',
            'name': "Simon",
            'email': 'testuser@example.com'
        }
        response = self.client.post('/api/add_user', json=valid_data)

        self.assertEqual(response.status_code, 401)

    def test_add_user_post_valid_authorised(self):
        """Test the /api/add_user endpoint with a valid POST request."""
        # Define a valid payload for adding a user
        valid_data = {
            'external_key': '643463',
            'name': "Simon",
            'email': 'testuser@example.com'
        }

        headers = {
            'token': 'complicated_token'
        }

        response = self.client.post('/api/add_user', json=valid_data, headers=headers)

        self.assertEqual(response.status_code, 201)

if __name__ == '__main__':
    unittest.main()