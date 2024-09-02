from pymongo import MongoClient
from pymongo.server_api import ServerApi
import dns.resolver
import dns

def main():
    # Set up dnspython resolver to use the specific DNS server
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8']  # Google's public DNS server

    # Patch dns.resolver.default_resolver to use the custom resolver
    dns.resolver.default_resolver = resolver

    # Create a new MongoClient instance, which connects to the MongoDB server
    client = MongoClient(
        "mongodb+srv://dzvinchukt:rm7Fl0r11pWwy481@cluster0.szgft.mongodb.net/",
        server_api=ServerApi('1')
    )

    try:
        # Access DB (creates one if not exists)
        db = client.book

        # adding documents to the collection cats (collection is created if not exists)
        db.cats.insert_many(
            [
                {
                    "name": "Barsik",
                    "age": 3,
                    "features": ["not litter trained", "sweet", "red"],
                },
                {
                    "name": "Lama",
                    "age": 2,
                    "features": ["litter trained", "aggressive", "grey"],
                },
                {
                    "name": "Liza",
                    "age": 4,
                    "features": ["litter trained", "sweet", "white"],
                },          
            ]
        )

        # Intro for user
        print('''Welcome to the cats store!
            Please print a command to see the information:
            all - to see all cats in DataBase
            cat - to see information about the exact cat
            age - to change the age of the exact cat
            feature - to add a feachure of the exact cat
            take cat - to take one exact cat home (he won't be at the store any more)
            take all - to take all cats home (store will be empty)
            exit - to exit a store
            ''')
        
        # interaction with the user
        while True:
            command = input("Enter a command: ").lower()
            if command == "exit":
                clear_all(db.cats)
                print("Good bye!")
                break
            elif command == "all":
                print_all(db.cats)
            elif command == "cat":
                print_cat(db.cats)
            elif command == "age":
                update_cat_age(db.cats)
            elif command == "feature":
                add_feature(db.cats)
            elif command == "take cat":
                delete_cat(db.cats)
            elif command == "take all":
                clear_all(db.cats)
                print("You took all cats! No more cats in the store! Good bye:)")
                break
            else:
                print("I don't understand this command")

    finally:
        # Ensure the client is closed when done
        client.close()

# Printing all documents from the collection
def print_all(cat_collection):
    all_cats = cat_collection.find({})
    print("Here are all cats:")
    for cat in all_cats:
        for key, value in cat.items():
            print(f"{key}: {value}")
        print()

# Printing information about the exact cat based on user input
def print_cat(cat_collection):
    name = input("Print a cat's name to see information about it: ")
    cat = cat_collection.find_one({"name": name})
    # if user inserts cat's name that is absent in the collection
    if cat is None:
        print("There is no such cat here")
    else:
        for key, value in cat.items():
            print(f"{key}: {value}")

# Updating cat's age based on user input
def update_cat_age(cat_collection):
    name = input("Print a cat's name to change his age: ")
    cat = cat_collection.find_one({"name": name})
    # if user inserts cat's name that is absent in the collection
    if cat is None:
        print("There is no such cat here")
        return None
    new_age = input("Print new age of the cat: ")
    # verifying if age is integer
    try:
        new_age = int(new_age)
        cat_collection.update_one({"name": name}, {"$set": {"age": new_age}})
        print(f"New age of {name} is {new_age}!")
    except ValueError:
        print("Age should be a number. Try again.")

# Adding a feature for a cat
def add_feature(cat_collection):
    name = input("Print a cat's name to add a feature: ")
    cat = cat_collection.find_one({"name": name})
    # if user inserts cat's name that is absent in the collection
    if cat is None:
        print("There is no such cat here")
        return None
    feature = input("Write a new feature of the cat: ")
    cat_collection.update_one({"name": name}, {"$push": {"features": feature}})
    print(f"Now {name} is {feature}")

# Deleting one cat from the collection
def delete_cat(cat_collection):
    name = input("Print the name of a cat you want to take home: ")
    cat = cat_collection.find_one({"name": name})
    # if user inserts cat's name that is absent in the collection
    if cat is None:
        print("There is no such cat here")
        return None
    cat_collection.delete_one({"name": name})
    print(f"Now {name} is your cat!")

# deleting all documents from the collection
def clear_all(cat_collection):
    cat_collection.delete_many({})


if __name__ == "__main__":
    main()
