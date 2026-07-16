import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          
        password="--",
        database="LibraryDB"  
    )

def save_book():
    title = book_title_input.get()
    author = book_author_input.get()
    copies = book_copies_input.get()
    
    if not title or not author or not copies:
        messagebox.showwarning("Warning", "Fill all fields")
        return
        
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("INSERT IGNORE INTO Authors (author_name) VALUES (%s)", (author,))
        db.commit()
        
        cursor.execute("SELECT author_id FROM Authors WHERE author_name = %s", (author,))
        author_id = cursor.fetchone()
        
        cursor.execute("INSERT INTO Books (title, author_id, available_copies) VALUES (%s, %s, %s)", 
                       (title, author_id[0], int(copies)))
        db.commit()
        
        messagebox.showinfo("Success", "Book & Author logged successfully!")
        book_title_input.delete(0, tk.END)
        book_author_input.delete(0, tk.END)
        book_copies_input.delete(0, tk.END)
        load_catalog()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        if 'db' in locals() and db.is_connected():
            db.close()

def delete_book():
    selected_item = catalog_grid.selection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please click on a book from the list below to select it first!")
        return
        
    row_data = catalog_grid.item(selected_item)['values']
    if not row_data:
        return
        
    book_id = row_data[0]
    book_title = row_data[1]
    
    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{book_title}'?\nThis will remove it from the system.")
    if confirm:
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("DELETE FROM Books WHERE book_id = %s", (int(book_id),))
            db.commit()
            messagebox.showinfo("Deleted", "Book successfully removed!")
            load_catalog() 
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")
        finally:
            if 'db' in locals() and db.is_connected():
                db.close()

def load_catalog():
    for row in catalog_grid.get_children():
        catalog_grid.delete(row)
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            SELECT b.book_id, b.title, a.author_name, b.available_copies 
            FROM Books b 
            LEFT JOIN Authors a ON b.author_id = a.author_id
        """)
        for book in cursor.fetchall():
            catalog_grid.insert("", tk.END, values=book)
    except Exception as e:
        print(f"Error loading catalog: {e}")
    finally:
        if 'db' in locals() and db.is_connected():
            db.close()

def issue_book():
    b_id = issue_book_id.get()
    m_id = issue_member_id.get()
    
    if not b_id or not m_id:
        messagebox.showwarning("Warning", "Fill all IDs")
        return
        
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("SELECT available_copies FROM Books WHERE book_id = %s", (b_id,))
        res = cursor.fetchone()
        
        if res and res[0] > 0:
            cursor.execute("INSERT INTO IssuedBooks (book_id, member_id) VALUES (%s, %s)", (b_id, m_id))
            cursor.execute("UPDATE Books SET available_copies = available_copies - 1 WHERE book_id = %s", (b_id,))
            db.commit()
            messagebox.showinfo("Success", "Book issued successfully!")
            issue_book_id.delete(0, tk.END)
            issue_member_id.delete(0, tk.END)
            load_catalog()
            load_loans()
        else:
            messagebox.showwarning("Out of Stock", "No copies available or Book ID invalid.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        if 'db' in locals() and db.is_connected():
            db.close()

def load_loans():
    for row in loan_grid.get_children():
        loan_grid.delete(row)
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            SELECT i.issue_id, b.title, m.member_name, i.issue_date, i.status 
            FROM IssuedBooks i
            JOIN Books b ON i.book_id = b.book_id
            JOIN Members m ON i.member_id = m.member_id
        """)
        for loan in cursor.fetchall():
            loan_grid.insert("", tk.END, values=loan)
    except Exception as e:
        print(f"Error loading loans: {e}")
    finally:
        if 'db' in locals() and db.is_connected():
            db.close()

def save_member():
    name = member_name_input.get()
    if not name:
        messagebox.showwarning("Warning", "Please enter a member name")
        return
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO Members (member_name) VALUES (%s)", (name,))
        db.commit()
        messagebox.showinfo("Success", f"Member '{name}' registered successfully!")
        member_name_input.delete(0, tk.END)
        load_members()
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        if 'db' in locals() and db.is_connected():
            db.close()

def load_members():
    for row in member_grid.get_children():
        member_grid.delete(row)
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT member_id, member_name, join_date FROM Members")
        for member in cursor.fetchall():
            member_grid.insert("", tk.END, values=member)
    except Exception as e:
        print(f"Error loading members: {e}")
    finally:
        if 'db' in locals() and db.is_connected():
            db.close()


root = tk.Tk()
root.title("Relational Library Database Dashboard")
root.geometry("600x600")

notebook = ttk.Notebook(root)
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
tab3 = ttk.Frame(notebook)

notebook.add(tab1, text=" Books & Authors Catalog ")
notebook.add(tab2, text=" Issue Tracker Log ")
notebook.add(tab3, text=" Manage Members ")
notebook.pack(expand=1, fill="both")

tk.Label(tab1, text="Register New Book Entry", font=("Arial", 11, "bold")).pack(pady=5)
tk.Label(tab1, text="Book Title:").pack()
book_title_input = tk.Entry(tab1, width=40); book_title_input.pack()
tk.Label(tab1, text="Author Name:").pack()
book_author_input = tk.Entry(tab1, width=40); book_author_input.pack()
tk.Label(tab1, text="Initial Stock Count:").pack()
book_copies_input = tk.Entry(tab1, width=40); book_copies_input.pack()

tk.Button(tab1, text="Save Book Data", command=save_book, bg="#2196F3", fg="white").pack(pady=10)

catalog_grid = ttk.Treeview(tab1, columns=("ID", "Title", "Author", "Copies"), show='headings', height=8)
catalog_grid.heading("ID", text="ID"); catalog_grid.column("ID", width=40)
catalog_grid.heading("Title", text="Book Title"); catalog_grid.column("Title", width=200)
catalog_grid.heading("Author", text="Author"); catalog_grid.column("Author", width=180)
catalog_grid.heading("Copies", text="Available"); catalog_grid.column("Copies", width=80)
catalog_grid.pack(pady=5)

tk.Button(tab1, text="Delete Selected Book", command=delete_book, bg="#F44336", fg="white", width=25).pack(pady=5)

tk.Label(tab2, text="Log Book Loan Authorization", font=("Arial", 11, "bold")).pack(pady=5)
tk.Label(tab2, text="Enter Target Book ID:").pack()
issue_book_id = tk.Entry(tab2, width=30); issue_book_id.pack()
tk.Label(tab2, text="Enter Target Member ID:").pack()
issue_member_id = tk.Entry(tab2, width=30); issue_member_id.pack()

tk.Button(tab2, text="Process Checkout Action", command=issue_book, bg="#FF9800", fg="white").pack(pady=10)

loan_grid = ttk.Treeview(tab2, columns=("ID", "Book", "Member", "Date", "Status"), show='headings', height=8)
loan_grid.heading("ID", text="Loan ID"); loan_grid.column("ID", width=60)
loan_grid.heading("Book", text="Book Borrowed"); loan_grid.column("Book", width=160)
loan_grid.heading("Member", text="Student Name"); loan_grid.column("Member", width=140)
loan_grid.heading("Date", text="Date Issued"); loan_grid.column("Date", width=100)
loan_grid.heading("Status", text="Status"); loan_grid.column("Status", width=80)
loan_grid.pack(pady=10)

tk.Label(tab3, text="Register New Library Member", font=("Arial", 11, "bold")).pack(pady=5)
tk.Label(tab3, text="Full Name:").pack()
member_name_input = tk.Entry(tab3, width=40); member_name_input.pack(pady=5)

tk.Button(tab3, text="Register Member", command=save_member, bg="#E91E63", fg="white").pack(pady=10)

member_grid = ttk.Treeview(tab3, columns=("MemberID", "Name", "JoinDate"), show='headings', height=8)
member_grid.heading("MemberID", text="Member ID"); member_grid.column("MemberID", width=100, anchor=tk.CENTER)
member_grid.heading("Name", text="Full Name"); member_grid.column("Name", width=250)
member_grid.heading("JoinDate", text="Join Date"); member_grid.column("JoinDate", width=150, anchor=tk.CENTER)
member_grid.pack(pady=10)

try:
    load_catalog()
    load_loans()
    load_members()
except Exception as init_err:
    print(f"Startup data fetch error skipped: {init_err}")

root.mainloop()
