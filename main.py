from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# --- Simplified LibraryManagementSystem Class for Flask ---
class LibrarySystem:
    def __init__(self):
        self.books = []
        self.members = []
        self.next_book_id = 1
        self.next_member_id = 1
        self.data_dir = 'data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.load_data()

    def load_data(self):
        # Load books
        books_file = os.path.join(self.data_dir, 'books.json')
        if os.path.exists(books_file):
            with open(books_file, 'r') as f:
                self.books = json.load(f)
        
        # Load members
        members_file = os.path.join(self.data_dir, 'members.json')
        if os.path.exists(members_file):
            with open(members_file, 'r') as f:
                self.members = json.load(f)
        
        # Load metadata
        metadata_file = os.path.join(self.data_dir, 'metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                self.next_book_id = metadata.get('next_book_id', len(self.books) + 1)
                self.next_member_id = metadata.get('next_member_id', len(self.members) + 1)

    def save_data(self):
        # Save books
        with open(os.path.join(self.data_dir, 'books.json'), 'w') as f:
            json.dump(self.books, f, indent=2)
        
        # Save members
        with open(os.path.join(self.data_dir, 'members.json'), 'w') as f:
            json.dump(self.members, f, indent=2)
        
        # Save metadata
        metadata = {
            'next_book_id': self.next_book_id,
            'next_member_id': self.next_member_id
        }
        with open(os.path.join(self.data_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

    # --- Methods for data manipulation (CRUD, borrow, etc.) ---
    def add_book(self, title, author, isbn, category):
        new_book = {
            'id': self.next_book_id,
            'title': title,
            'author': author,
            'isbn': isbn,
            'category': category,
            'status': 'available',
            'borrowed_by': None,
            'borrow_date': None
        }
        self.books.append(new_book)
        self.next_book_id += 1
        self.save_data()

    def get_book(self, book_id):
        return next((b for b in self.books if b['id'] == book_id), None)

    def update_book(self, book_id, data):
        book = self.get_book(book_id)
        if book:
            book.update(data)
            self.save_data()
            return True
        return False
    
    def delete_book(self, book_id):
        self.books = [b for b in self.books if b['id'] != book_id]
        self.save_data()

    def add_member(self, name, email, phone):
        new_member = {
            'id': self.next_member_id,
            'name': name,
            'email': email,
            'phone': phone,
            'membership_date': datetime.now().strftime('%Y-%m-%d'),
            'borrowed_books': []
        }
        self.members.append(new_member)
        self.next_member_id += 1
        self.save_data()

    def get_member(self, member_id):
        return next((m for m in self.members if m['id'] == member_id), None)

    def update_member(self, member_id, data):
        member = self.get_member(member_id)
        if member:
            member.update(data)
            self.save_data()
            return True
        return False

    def delete_member(self, member_id):
        self.members = [m for m in self.members if m['id'] != member_id]
        self.save_data()

    def borrow_book(self, book_id, member_id):
        book = self.get_book(book_id)
        member = self.get_member(member_id)
        if book and member and book['status'] == 'available':
            book['status'] = 'borrowed'
            book['borrowed_by'] = member['name']
            book['borrow_date'] = datetime.now().strftime('%Y-%m-%d')
            member['borrowed_books'].append(book['title'])
            self.save_data()
            return True
        return False

    def return_book(self, book_id, fine_per_day=10, max_days=14):
    book = self.get_book(book_id)
    if book and book['status'] == 'borrowed':
        borrowed_by = book['borrowed_by']
        member = next((m for m in self.members if m['name'] == borrowed_by), None)

        borrow_date = datetime.strptime(book['borrow_date'], '%Y-%m-%d')
        return_date = datetime.now()
        days_borrowed = (return_date - borrow_date).days

        fine = 0
        if days_borrowed > max_days:
            fine = (days_borrowed - max_days) * fine_per_day

        # Update book details
        book['status'] = 'available'
        book['borrowed_by'] = None
        book['return_date'] = return_date.strftime('%Y-%m-%d')
        book['days_borrowed'] = days_borrowed
        book['fine'] = fine

        # Update member record
        if member and book['title'] in member['borrowed_books']:
            member['borrowed_books'].remove(book['title'])

        self.save_data()
        return {"days_borrowed": days_borrowed, "fine": fine}

    return None

    
    def get_stats(self):
        return {
            'total_books': len(self.books),
            'available_books': len([b for b in self.books if b['status'] == 'available']),
            'borrowed_books': len([b for b in self.books if b['status'] == 'borrowed']),
            'total_members': len(self.members)
        }

    def get_recent_activity(self):
        return [b for b in self.books if b['status'] == 'borrowed']

library_system = LibrarySystem()

@app.route('/')
def dashboard():
    stats = library_system.get_stats()
    recent_activity = library_system.get_recent_activity()
    return render_template('dashboard.html', stats=stats, recent_activity=recent_activity)

@app.route('/books')
def books():
    search_term = request.args.get('search', '').lower()
    if search_term:
        filtered_books = [b for b in library_system.books if
                          search_term in b['title'].lower() or
                          search_term in b['author'].lower()]
    else:
        filtered_books = library_system.books
    return render_template('books.html', books=filtered_books, search_term=search_term)

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        category = request.form['category']
        library_system.add_book(title, author, isbn, category)
        return redirect(url_for('books'))
    return render_template('book_form.html')

@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = library_system.get_book(book_id)
    if not book:
        return redirect(url_for('books'))
    if request.method == 'POST':
        data = {
            'title': request.form['title'],
            'author': request.form['author'],
            'isbn': request.form['isbn'],
            'category': request.form['category']
        }
        library_system.update_book(book_id, data)
        return redirect(url_for('books'))
    return render_template('book_form.html', book=book)

@app.route('/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    library_system.delete_book(book_id)
    return redirect(url_for('books'))

@app.route('/members')
def members():
    search_term = request.args.get('search', '').lower()
    if search_term:
        filtered_members = [m for m in library_system.members if
                            search_term in m['name'].lower() or
                            search_term in m['email'].lower()]
    else:
        filtered_members = library_system.members
    return render_template('members.html', members=filtered_members, search_term=search_term)

@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        library_system.add_member(name, email, phone)
        return redirect(url_for('members'))
    return render_template('member_form.html')

@app.route('/members/edit/<int:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    member = library_system.get_member(member_id)
    if not member:
        return redirect(url_for('members'))
    if request.method == 'POST':
        data = {
            'name': request.form['name'],
            'email': request.form['email'],
            'phone': request.form['phone']
        }
        library_system.update_member(member_id, data)
        return redirect(url_for('members'))
    return render_template('member_form.html', member=member)

@app.route('/members/delete/<int:member_id>', methods=['POST'])
def delete_member(member_id):
    member = library_system.get_member(member_id)
    if member and not member['borrowed_books']:
        library_system.delete_member(member_id)
    return redirect(url_for('members'))

@app.route('/transactions')
def transactions():
    fine_per_day = 10   # you can move this to settings.json later
    max_days = 14

    transactions_list = [
        {
            'book_title': b['title'],
            'borrowed_by': b['borrowed_by'],
            'borrow_date': b.get('borrow_date'),
            'return_date': b.get('return_date'),
            'days_borrowed': b.get('days_borrowed'),
            'fine': b.get('fine', 0),
            'status': b['status'].title()
        } for b in library_system.books if b.get('borrow_date')
    ]
    return render_template(
        'transactions.html',
        transactions=transactions_list,
        fine_per_day=fine_per_day,
        max_days=max_days
    )



@app.route('/borrow/<int:book_id>')
def borrow(book_id):
    book = library_system.get_book(book_id)
    if not book or book['status'] != 'available':
        return redirect(url_for('books'))
    return render_template('borrow.html', book=book, members=library_system.members)

@app.route('/borrow/<int:book_id>/confirm', methods=['POST'])
def confirm_borrow(book_id):
    member_id = int(request.form['member_id'])
    library_system.borrow_book(book_id, member_id)
    return redirect(url_for('books'))

@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    library_system.return_book(book_id)
    return redirect(url_for('books'))

if __name__ == '__main__':
    # Initial data for a new application run
    if not os.path.exists('data/books.json'):
        # This initial data setup is for demonstration purposes
        initial_books = [
            {'id': 1, 'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'isbn': '978-0-7432-7356-5', 'category': 'Fiction', 'status': 'available', 'borrowed_by': None, 'borrow_date': None, 'return_date': None},
            {'id': 2, 'title': 'To Kill a Mockingbird', 'author': 'Harper Lee', 'isbn': '978-0-06-112008-4', 'category': 'Fiction', 'status': 'borrowed', 'borrowed_by': 'John Doe', 'borrow_date': '2024-09-15', 'return_date': None},
            {'id': 3, 'title': 'Introduction to Algorithms', 'author': 'Thomas H. Cormen', 'isbn': '978-0-262-03384-8', 'category': 'Computer Science', 'status': 'available', 'borrowed_by': None, 'borrow_date': None, 'return_date': None}
        ]
        initial_members = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'phone': '+1-234-567-8900', 'membership_date': '2024-01-15', 'borrowed_books': ['To Kill a Mockingbird']},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'phone': '+1-234-567-8901', 'membership_date': '2024-02-20', 'borrowed_books': []},
            {'id': 3, 'name': 'Bob Johnson', 'email': 'bob@example.com', 'phone': '+1-234-567-8902', 'membership_date': '2024-03-10', 'borrowed_books': []}
        ]
        with open('data/books.json', 'w') as f:
            json.dump(initial_books, f, indent=2)
        with open('data/members.json', 'w') as f:
            json.dump(initial_members, f, indent=2)

    app.run(debug=True)
