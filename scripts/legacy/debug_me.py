def count_down(start):
    for number in range(start, 0, -1):
        print(f"{number}...")
    print("Blast off!")

def main():
    user_input = input("Enter a number to start countdown: ")
    count_down(user_input)

main() 