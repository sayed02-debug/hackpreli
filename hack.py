class BookManager:
    def __init__(self):
        self.books = set()

    def add_book(self, title):
        """Add a book title to the set."""
        if title in self.books:
            print(f'"{title}" already exists.')
        else:
            self.books.add(title)
            print(f'"{title}" added.')

    def remove_book(self, title):
        """Remove a book title from the set."""
        if title in self.books:
            self.books.remove(title)
            print(f'"{title}" removed.')
        else:
            print(f'"{title}" not found.')

    def list_books(self):
        """List all book titles."""
        if not self.books:
            print("No books in the collection.")
        else:
            print("Books in collection:")
            for book in sorted(self.books):
                print(f"- {book}")

# Example usage
if __name__ == "__main__":
    manager = BookManager()
    manager.add_book("1984")
    manager.add_book("Brave New World")
    manager.add_book("1984")  # Duplicate
    manager.list_books()
    manager.remove_book("1984")
    manager.list_books()