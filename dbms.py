from pymongo import MongoClient
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

class StudentGradeDB:
    def __init__(self, db_name="student_grades", collection_name="grades"):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def add_student(self, student_id, name, email, phone, department, year):
        if self.collection.find_one({"student_id": student_id}):
            raise ValueError("Student ID already exists")
        student_data = {
            "student_id": student_id,
            "name": name,
            "email": email,
            "phone": phone,
            "department": department,
            "year": year,
            "courses": []
        }
        self.collection.insert_one(student_data)
        return "Student added successfully"

    def add_course(self, student_id, course_name, grade):
        if not 0 <= grade <= 100:
            raise ValueError("Grade must be between 0 and 100")
        result = self.collection.update_one(
            {"student_id": student_id},
            {"$push": {"courses": {"name": course_name, "grade": grade}}}
        )
        if result.modified_count == 0:
            raise ValueError("Student not found")
        return "Course added successfully"

    def get_student(self, student_id):
        return self.collection.find_one({"student_id": student_id}, {"_id": 0})

    def get_all_students(self):
        return list(self.collection.find({}, {"_id": 0}))

    def calculate_gpa(self, student_id):
        student = self.get_student(student_id)
        if not student or not student.get("courses"):
            return None

        def grade_to_unit_and_letter(grade):
            if grade >= 90: return 10, "A+"
            elif grade >= 80: return 9, "A"
            elif grade >= 70: return 8, "B"
            elif grade >= 60: return 7, "C"
            elif grade >= 50: return 6, "D"
            elif grade >= 40: return 5, "E"
            else: return 0, "F"

        total_unit = 0
        letter_grades = []

        for course in student["courses"]:
            unit, letter = grade_to_unit_and_letter(course["grade"])
            total_unit += unit
            letter_grades.append(letter)

        avg_unit = round(total_unit / len(student["courses"]), 2)
        return {"unit_gpa": avg_unit, "letter": max(letter_grades, key=letter_grades.count)}

    def close_connection(self):
        self.client.close()


class LoginPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Student Grade Database")
        self.root.geometry("420x460")  # Increased height and width for layout
        self.db = StudentGradeDB()

        self.frame = Frame(self.root, bg="#e0f7fa")
        self.frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # Load and display larger logo
        try:
            self.logo_img = Image.open("logo.png")
            self.logo_img = self.logo_img.resize((380, 140))  # Increased size
            self.logo_photo = ImageTk.PhotoImage(self.logo_img)
            Label(self.frame, image=self.logo_photo, bg="#e0f7fa").pack(pady=(30, 20))  # More spacing below image
        except Exception as e:
            print("Logo not found or error loading logo:", e)

        # Title
        Label(self.frame, text="Student Grade Database", font=("Segoe UI", 20, "bold"), bg="#e0f7fa").pack(pady=(0, 30))

        # Role selector
        Label(self.frame, text="Role", bg="#e0f7fa", anchor="w", font=("Segoe UI", 12)).pack()
        self.role_var = StringVar(value="Admin")
        OptionMenu(self.frame, self.role_var, "Admin", "Student").pack(pady=5)

        # Username
        Label(self.frame, text="Username / ID", bg="#e0f7fa", anchor="w", font=("Segoe UI", 12)).pack()
        self.username_entry = Entry(self.frame, font=("Segoe UI", 12))
        self.username_entry.pack()

        # Password
        Label(self.frame, text="Password", bg="#e0f7fa", anchor="w", font=("Segoe UI", 12)).pack()
        self.password_entry = Entry(self.frame, show="*", font=("Segoe UI", 12))
        self.password_entry.pack()

        # Login Button
        Button(self.frame, text="Login", command=self.login, bg="#00796b", fg="white", font=("Segoe UI", 12, "bold")).pack(pady=20)

    def login(self):
        role = self.role_var.get()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if role == "Admin":
            if username == "admin" and password == "admin123":
                self.root.destroy()
                root = Tk()
                GradeBookApp(root)
                root.mainloop()
            else:
                messagebox.showerror("Login Failed", "Invalid Admin credentials.")
        elif role == "Student":
            student = self.db.get_student(username)
            if student:
                self.root.destroy()
                root = Tk()
                StudentViewApp(root, student)
                root.mainloop()
            else:
                messagebox.showerror("Login Failed", "Student ID not found.")
        else:
            messagebox.showerror("Login Failed", "Please choose a valid role.")


class GradeBookApp:
    def __init__(self, root):
        self.root = root
        self.db = StudentGradeDB()
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Student Grade Database - Admin")
        self.root.geometry("1200x750")
        self.root.configure(bg="#e0f7fa")

        Label(self.root, text="Student Grade Database", font=("Segoe UI", 20, "bold"),
              bg="#004d40", fg="white", pady=10).pack(fill=X)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.create_student_tab()
        self.create_course_tab()
        self.create_view_tab()
        self.create_search_tab()

    def create_student_tab(self):
        tab = Frame(self.notebook, bg='white')
        self.notebook.add(tab, text="Add Student")

        labels = ["Student ID", "Name", "Email", "Phone", "Department", "Year"]
        self.entries = []

        for i, label in enumerate(labels):
            Label(tab, text=label + ":", bg='white', font=("Segoe UI", 11)).grid(row=i, column=0, padx=10, pady=8, sticky='e')
            entry = Entry(tab, bg="#e0f2f1", font=("Segoe UI", 11))
            entry.grid(row=i, column=1, padx=10, pady=8, sticky='w')
            self.entries.append(entry)

        Button(tab, text="Add Student", command=self.add_student, bg="#00796b", fg="white", font=("Segoe UI", 11)).grid(row=6, columnspan=2, pady=15)

    def create_course_tab(self):
        tab = Frame(self.notebook, bg='white')
        self.notebook.add(tab, text="Add Course")

        self.course_entries = []
        for i, label in enumerate(["Student ID", "Course Name", "Grade (0-100)"]):
            Label(tab, text=label + ":", bg='white', font=("Segoe UI", 11)).grid(row=i, column=0, padx=10, pady=8, sticky='e')
            entry = Entry(tab, bg="#e0f2f1", font=("Segoe UI", 11))
            entry.grid(row=i, column=1, padx=10, pady=8, sticky='w')
            self.course_entries.append(entry)

        Button(tab, text="Add Course", command=self.add_course, bg="#00796b", fg="white", font=("Segoe UI", 11)).grid(row=3, columnspan=2, pady=15)

    def create_view_tab(self):
        tab = Frame(self.notebook, bg='white')
        self.notebook.add(tab, text="View All Students")

        self.tree = ttk.Treeview(tab, columns=("ID", "Name", "Email", "Phone", "Dept", "Year", "Courses", "Marks", "GPA"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=W, width=120)
        self.tree.pack(fill=BOTH, expand=True, pady=10)

        Button(tab, text="Refresh", command=self.load_data, bg="#00796b", fg="white", font=("Segoe UI", 11)).pack(pady=10)
        self.load_data()

    def create_search_tab(self):
        tab = Frame(self.notebook, bg='white')
        self.notebook.add(tab, text="Search Student")

        Label(tab, text="Enter Student ID:", bg='white', font=("Segoe UI", 12)).pack(pady=10)
        self.search_id_entry = Entry(tab, font=("Segoe UI", 12), bg="#e0f2f1")
        self.search_id_entry.pack(pady=5)

        Button(tab, text="Search", command=self.search_student, bg="#00796b", fg="white", font=("Segoe UI", 11)).pack(pady=10)

        self.search_result_text = Text(tab, font=("Segoe UI", 10), width=100, height=15, bg="#f1f8e9")
        self.search_result_text.pack(pady=10, padx=20)

    def add_student(self):
        try:
            values = [e.get() for e in self.entries]
            if not all(values):
                messagebox.showerror("Error", "All fields are required")
                return
            messagebox.showinfo("Success", self.db.add_student(*values))
            for e in self.entries:
                e.delete(0, END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_course(self):
        try:
            sid, cname, grade = [e.get() for e in self.course_entries]
            messagebox.showinfo("Success", self.db.add_course(sid, cname, float(grade)))
            for e in self.course_entries:
                e.delete(0, END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        for student in self.db.get_all_students():
            courses = ", ".join([c["name"] for c in student["courses"]])
            marks = ", ".join([str(c["grade"]) for c in student["courses"]])
            gpa = self.db.calculate_gpa(student["student_id"])
            gpa_str = f'{gpa["unit_gpa"]} ({gpa["letter"]})' if gpa else "N/A"
            self.tree.insert('', 'end', values=(
                student["student_id"], student["name"], student["email"],
                student["phone"], student["department"], student["year"],
                courses, marks, gpa_str
            ))

    def search_student(self):
        student_id = self.search_id_entry.get().strip()
        self.search_result_text.delete(1.0, END)

        if not student_id:
            self.search_result_text.insert(END, "Please enter a Student ID.")
            return

        student = self.db.get_student(student_id)
        if not student:
            self.search_result_text.insert(END, "Student not found.")
            return

        gpa_info = self.db.calculate_gpa(student_id)
        gpa_str = f'{gpa_info["unit_gpa"]} ({gpa_info["letter"]})' if gpa_info else "N/A"

        result = (
            f"Student ID: {student['student_id']}\n"
            f"Name: {student['name']}\n"
            f"Email: {student['email']}\n"
            f"Phone: {student['phone']}\n"
            f"Department: {student['department']}\n"
            f"Year: {student['year']}\n"
            f"GPA: {gpa_str}\n\n"
            f"Courses & Grades:\n"
        )

        for course in student.get("courses", []):
            result += f"  - {course['name']}: {course['grade']}\n"

        self.search_result_text.insert(END, result)


class StudentViewApp:
    def __init__(self, root, student):
        self.root = root
        self.db = StudentGradeDB()
        self.student = student
        self.root.title("Student View - Grade Database")
        self.root.geometry("700x500")
        self.root.configure(bg="#f1f8e9")

        Label(self.root, text=f"Welcome, {student['name']}", font=("Segoe UI", 16, "bold"), bg="#aed581").pack(pady=20)

        gpa_info = self.db.calculate_gpa(student["student_id"])
        gpa_text = f'{gpa_info["unit_gpa"]} ({gpa_info["letter"]})' if gpa_info else "N/A"

        Label(self.root, text=f"GPA: {gpa_text}", font=("Segoe UI", 14), bg="#f1f8e9").pack(pady=10)

        text_box = Text(self.root, font=("Segoe UI", 10), width=80, height=15)
        text_box.pack(padx=20, pady=10)

        for course in student["courses"]:
            text_box.insert(END, f"{course['name']}: {course['grade']}\n")


if __name__ == "__main__":
    root = Tk()
    LoginPage(root)
    root.mainloop()
