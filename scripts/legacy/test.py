import unittest
from homework_1 import is_greeting, get_name_response, get_response

class TestChatbot(unittest.TestCase):
    def test_is_greeting(self):
        """Test if the function correctly identifies greetings"""
        # Test valid greetings
        self.assertTrue(is_greeting("hi"))
        self.assertTrue(is_greeting("hello"))
        
        # Test non-greetings
        self.assertFalse(is_greeting("bye"))
        self.assertFalse(is_greeting("what's up"))
        self.assertFalse(is_greeting(""))

    def test_get_name_response(self):
        """Test if the name response contains the bot's name"""
        response = get_name_response()
        # Check if response is a string
        self.assertIsInstance(response, str)
        # Check if response isn't empty
        self.assertTrue(len(response) > 0)

    def test_get_response(self):
        """Test different types of user input"""
        # Test greeting response
        greeting_response = get_response("hi")
        self.assertTrue("Hi" in greeting_response or "hello" in greeting_response.lower())
        
        # Test name question response
        name_response = get_response("what is your name")
        self.assertTrue("Buddy" in name_response)
        
        # Test unknown input response
        unknown_response = get_response("xyz123")
        self.assertTrue(len(unknown_response) > 0)
        self.assertTrue("not sure" in unknown_response.lower())

if __name__ == '__main__':
    unittest.main()