"""
Introduction to Python - Homework 1: Building a Simple Chatbot

Overview:
This homework will help you practice using Python's basic building blocks - functions,
if/else statements, and while loops - to create an interactive chatbot. A chatbot
is a program that can have a conversation with a user through text.

Goals:
- Practice writing and using functions
- Get comfortable with if/else statements for making decisions
- Use while loops for repeating actions
- Build something fun that you can show to friends and family!

Instructions:
1. Read through all the function descriptions carefully
2. Fill in the code for each function where it says "TODO"
3. Test your chatbot by running this file and having conversations with it
4. Additionally, you can test your functions by running the test.py file
5. Make sure your chatbot can:
  - Say hello when you greet it
  - Tell you its name when you ask
  - Play a number guessing game
  - Handle any other input politely

Getting Started:
1. Fill in is_greeting() first - this is the simplest function
2. Then do get_name_response() - you just need to return a string
3. The play_number_game() function lets you practice while loops
4. Finally, get_response() puts everything together using if/elif/else

Remember:
- Test your code frequently to catch errors early
- Ask for help if you get stuck! Programming is collaborative
- Have fun and be creative with your chatbot's personality

Example Conversation:
Bot: Hello! I'm a chatbot. Type 'quit' to exit.
You: hi
Bot: Hi there! Nice to meet you!
You: what is your name
Bot: I'm Buddy the Bot!
You: let's play a game
Bot: I'm thinking of a number. Try to guess it!
You: 3
Bot: Too low! Guess again:
You: 5
Bot: You got it! The number was 5!
You: quit
Bot: Goodbye!
"""

import random

def is_greeting(user_input):
    """
    Check if the user's input is a greeting.
    
    Args:
        user_input (str): The user's input, converted to lowercase
    
    Returns:
        bool: True if user types "hi" or "hello", False otherwise
    
    Example:
        >>> is_greeting("hello")
        True
        >>> is_greeting("goodbye") 
        False
    """
    # TODO: Return True if user_input is "hi" or "hello"
    # Hint: use == to check if strings are equal
    # Hint: use or to check multiple conditions
    return user_input == "hi" or user_input == "hello"

def get_name_response():
    """
    Return a message telling the user this chatbot's name.
    
    Returns:
        str: A message containing this chatbot's name
        
    Example:
        >>> get_name_response()
        "My name is ChatBot!"
    """
    # TODO: Return a string that tells the user your chatbot's name
    # Be creative! Give your chatbot a fun name and personality
    return "My name is ChatBot, nice to meet you!"

def play_number_game():
    """
    Play a number guessing game with the user. Ask them to guess
    the random number. Keep asking until they get it right. The number must be between 1 and 10.
    
    Returns:
        str: A congratulations message
        
    Example interaction:
        Bot: I'm thinking of a number. Try to guess it!
        User: 3
        Bot: Too low! Guess again:
        User: 8 
        Bot: Too high! Guess again:
        User: 5
        Bot: You got it! The number was 5!
    """
    print("I'm thinking of a number. Try to guess it!")
    
    # TODO: Write a while loop that:
    # 1. Gets a number from the user (use input() and int())
    # 2. Prints "Too high!" if their guess is above the number
    # 3. Prints "Too low!" if their guess is below the number
    # 4. Breaks the loop and returns a winning message if they guess the number
    # HINT: Use random.randint to generate a random number between 1 and 10. You may search online for how to use this function.
    
    number = random.randint(1, 10)
    
    while True:
        guess = int(input("Please enter your guess: "))
        
        if guess > number:
            print("Too high! Try again:")
        elif guess < number:
            print("Too low! Try again:")
        else:
            return f"You got it! The number was {number}!"

def get_response(user_input):
    """
    Generate a response to the user's input.
    
    Args:
        user_input (str): The user's input
    
    Returns:
        str: The chatbot's response
    """
    # Convert to lowercase for easier matching
    user_input = user_input.lower()
    
    # TODO: Add if/elif/else statements to:
    # 1. Check if the input is "hi" or "hello" using is_greeting()
    # 2. Check if the input contains "what is your name" - call get_name_response()
    # 3. Check if the input is "play a game" - call play_number_game()
    # 4. Have a default response for any other input
    # HINT: to check if a string contains another string, use the key word "in." For example, "cat" in "caterpillar" will return True.
    
    if is_greeting(user_input):
        return "Hello! Nice to meet you!"
    elif "what is your name" in user_input or "your name" in user_input:
        return get_name_response()
    elif "play a game" in user_input or "game" in user_input:
        return play_number_game()
    else:
        return "I don't understand your input, but I'm happy to chat with you! You can greet me, ask my name, or play a guessing game.Please try again."

def chat():
    """
    Main chat loop that gets input from the user and prints responses.
    """
    print("Bot: Hello! I'm a chatbot. Type 'quit' to exit.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Bot: Goodbye!")
            break
            
        response = get_response(user_input)
        print("Bot:", response)

# Start the chat
if __name__ == "__main__":
    chat()