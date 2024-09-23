import requests
import json

BASE_URL = ''  # Modify if your API runs on a different port or host
AUTH_TOKEN = ''      # Replace with your actual token

# Common headers including the authorization token
HEADERS = {
    'Authorization': f'Bearer {AUTH_TOKEN}',
    'Content-Type': 'application/json'
}

def print_test_result(test_name, passed):
    print(f"Test {test_name}: {'PASSED' if passed else 'FAILED'}")

def test_add_user(external_key, name, email):
    url = f"{BASE_URL}/users"
    data = {
        "external_key": external_key,
        "name": name,
        "email": email
    }
    response = requests.post(url, json=data, headers=HEADERS)
    print(response.json())
    passed = response.status_code == 201 and 'message' in response.json()
    print_test_result('Add User', passed)
    return passed

def test_get_user(external_key):
    url = f"{BASE_URL}/users/{external_key}"
    response = requests.get(url, headers=HEADERS)
    print(response.json())
    passed = response.status_code == 200 and 'external_key' in response.json()
    print_test_result('Get User', passed)
    return response.json() if passed else None

def test_update_user(external_key, new_name, new_email):
    url = f"{BASE_URL}/users/{external_key}"
    data = {
        "external_key": external_key,
        "name": new_name,
        "email": new_email
    }
    response = requests.put(url, json=data, headers=HEADERS)
    print(response.json())
    passed = response.status_code == 200 and 'message' in response.json()
    print_test_result('Update User', passed)
    return passed

def test_get_user_subscriptions(external_key):
    url = f"{BASE_URL}/users/{external_key}/subscriptions"
    response = requests.get(url, headers=HEADERS)
    print(response.json())
    passed = response.status_code == 200 and 'lists' in response.json()
    print_test_result('Get User Subscriptions', passed)
    return response.json() if passed else None

def test_add_subscription(external_key, list_id):
    url = f"{BASE_URL}/users/{external_key}/subscriptions"
    data = {"list_id": list_id}
    response = requests.post(url, json=data, headers=HEADERS)
    print(response.json())
    passed = response.status_code == 201 and 'message' in response.json()
    print_test_result('Add Subscription', passed)
    return passed

def test_remove_subscription(external_key, list_id):
    url = f"{BASE_URL}/users/{external_key}/subscriptions/{list_id}"
    response = requests.delete(url, headers=HEADERS)
    print(response.json())
    passed = response.status_code == 200 and 'message' in response.json()
    print_test_result('Remove Subscription', passed)
    return passed

def test_get_feedback_lists():
    url = f"{BASE_URL}/lists"
    response = requests.get(url, headers=HEADERS)
    print(response.json())
    passed = response.status_code == 200 and 'lists' in response.json()
    print_test_result('Get Feedback Lists', passed)
    return response.json() if passed else None

def run_tests():
    # Test data
    external_key = "user_test_123"
    name = "John Test"
    email = "johntest@example.com"
    updated_name = "John Test Updated"
    updated_email = "johnupdated@example.com"
    list_id = 1  # Use an existing list_id from your database or modify this

    # Running test cases
    print("\nRunning API Tests...\n")

    # Test: Add User
    if test_add_user(external_key, name, email):
        
        #meant to fail
        test_add_user(external_key, name, email)

        # Test: Get User
        test_get_user(external_key)

        # Test: Update User
        test_update_user(external_key, updated_name, updated_email)

        # Test: Get User Subscriptions
        test_get_user_subscriptions(external_key)

        # Test: Add Subscription
        test_add_subscription(external_key, list_id)

        #meant to fail
        test_add_subscription(external_key, list_id)

        # Test: Get User Subscriptions after adding one
        test_get_user_subscriptions(external_key)

        # Test: Remove Subscription
        test_remove_subscription(external_key, list_id)

        # Test: Add Subscription
        test_add_subscription(external_key, list_id)

        # Test: Get Feedback Lists
        test_get_feedback_lists()

if __name__ == "__main__":
    run_tests()
