import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Page Config
st.set_page_config(
    page_title="Advanced School Management System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database Connection
conn = sqlite3.connect("school.db", check_same_thread=False)
c = conn.cursor()

# Create Tables
c.execute('''CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT NOT NULL UNIQUE,
    class TEXT,
    section TEXT,
    age INTEGER,
    phone TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    teacher_id TEXT NOT NULL UNIQUE,
    subject TEXT,
    phone TEXT,
    email TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    status TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    amount REAL,
    payment_date TEXT,
    status TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_name TEXT,
    class TEXT,
    subject TEXT,
    max_marks INTEGER,
    date TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    exam_id INTEGER,
    marks_obtained INTEGER,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(exam_id) REFERENCES exams(id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    isbn TEXT UNIQUE,
    total_copies INTEGER DEFAULT 1,
    available_copies INTEGER
)''')

c.execute('''CREATE TABLE IF NOT EXISTS library_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    student_id INTEGER,
    issue_date TEXT,
    return_date TEXT,
    status TEXT,
    FOREIGN KEY(book_id) REFERENCES books(id),
    FOREIGN KEY(student_id) REFERENCES students(id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class TEXT,
    day TEXT,
    period INTEGER,
    subject TEXT,
    teacher TEXT
)''')

conn.commit()

# Sidebar Navigation
st.sidebar.title("🏫 School Management System")
page = st.sidebar.radio("Select Module", [
    "🏠 Dashboard",
    "👨‍🎓 Students",
    "👩‍🏫 Teachers",
    "📅 Attendance",
    "💰 Fees Management",
    "📊 Exams & Results",
    "📚 Library",
    "🗓️ Timetable"
])

# ========================
# DASHBOARD
# ========================
if page == "🏠 Dashboard":
    st.title("🏫 School Management Dashboard")
    st.markdown("### 📊 Overview")

    c.execute("SELECT COUNT(*) FROM students"); total_students = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM teachers"); total_teachers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM books"); total_books = c.fetchone()[0]
    c.execute("SELECT SUM(amount) FROM fees WHERE status = 'Pending'"); due_fees = c.fetchone()[0] or 0
    c.execute(f"SELECT COUNT(*) FROM attendance WHERE date = '{date.today()}' AND status = 'Present'"); present_today = c.fetchone()[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Students", total_students)
    col2.metric("Total Teachers", total_teachers)
    col3.metric("Books in Library", total_books)
    col4.metric("Pending Fees (₹)", due_fees)
    col5.metric("Present Today", present_today)

    st.success("System running smoothly! Use sidebar to manage modules.")

# ========================
# STUDENTS
# ========================
elif page == "👨‍🎓 Students":
    st.title("👨‍🎓 Student Management")

    tab1, tab2 = st.tabs(["➕ Add Student", "📋 View Students"])

    with tab1:
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Name *")
            roll_no = col2.text_input("Roll No *").upper()
            class_name = col1.text_input("Class")
            section = col2.text_input("Section").upper()
            age = col1.number_input("Age", 5, 30)
            phone = col2.text_input("Phone")

            submitted = st.form_submit_button("Add Student")
            if submitted:
                if name and roll_no:
                    try:
                        c.execute("INSERT INTO students (name, roll_no, class, section, age, phone) VALUES (?, ?, ?, ?, ?, ?)",
                                  (name, roll_no, class_name, section, age, phone))
                        conn.commit()
                        st.success(f"✅ {name} added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("❌ Roll No already exists!")
                else:
                    st.warning("⚠️ Name and Roll No are required!")

    with tab2:
        df = pd.read_sql_query("SELECT name, roll_no, class, section, age, phone FROM students", conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No students registered yet.")

# ========================
# TEACHERS
# ========================
elif page == "👩‍🏫 Teachers":
    st.title("👩‍🏫 Teacher Management")

    tab1, tab2 = st.tabs(["➕ Add Teacher", "📋 View Teachers"])

    with tab1:
        with st.form("add_teacher"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Name *")
            teacher_id = col2.text_input("Teacher ID *").upper()
            subject = col1.text_input("Subject")
            phone = col2.text_input("Phone")
            email = col1.text_input("Email")

            if st.form_submit_button("Add Teacher"):
                if name and teacher_id:
                    try:
                        c.execute("INSERT INTO teachers (name, teacher_id, subject, phone, email) VALUES (?, ?, ?, ?, ?)",
                                  (name, teacher_id, subject, phone, email))
                        conn.commit()
                        st.success("Teacher added!")
                    except sqlite3.IntegrityError:
                        st.error("Teacher ID exists!")
                else:
                    st.warning("Required fields missing!")

    with tab2:
        df = pd.read_sql_query("SELECT name, teacher_id, subject, phone, email FROM teachers", conn)
        st.dataframe(df, use_container_width=True) if not df.empty else st.info("No teachers yet.")

# ========================
# ATTENDANCE
# ========================
elif page == "📅 Attendance":
    st.title("📅 Attendance Management")
    attendance_date = st.date_input("Select Date", date.today())
    selected_date = str(attendance_date)

    students = pd.read_sql_query("SELECT id, name, roll_no FROM students", conn)

    if not students.empty:
        with st.form("mark_attendance"):
            st.subheader(f"Mark Attendance - {selected_date}")
            records = []
            for _, student in students.iterrows():
                status = st.selectbox(f"{student['name']} ({student['roll_no']})", ["Present", "Absent", "Late"], key=student['id'])
                records.append((student['id'], selected_date, status))

            if st.form_submit_button("Save Attendance"):
                c.executemany("INSERT OR REPLACE INTO attendance (student_id, date, status) VALUES (?, ?, ?)", records)
                conn.commit()
                st.success("Attendance saved!")

        # View
        view_df = pd.read_sql_query(f"""
            SELECT s.name, s.roll_no, a.status FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = '{selected_date}'
        """, conn)
        st.dataframe(view_df) if not view_df.empty else st.info("No record for this date.")
    else:
        st.warning("Add students first!")

# ========================
# FEES MANAGEMENT
# ========================
elif page == "💰 Fees Management":
    st.title("💰 Fees Management")

    tab1, tab2 = st.tabs(["Record Payment", "View Dues"])

    with tab1:
        students = pd.read_sql_query("SELECT id, name, roll_no FROM students", conn)
        if not students.empty:
            student_option = st.selectbox("Select Student", students["name"] + " - " + students["roll_no"])
            student_id = students.loc[students["name"] + " - " + students["roll_no"] == student_option, "id"].values[0]
            amount = st.number_input("Amount Paid (₹)", min_value=0.0, step=500.0)
            if st.button("Record Payment"):
                c.execute("INSERT INTO fees (student_id, amount, payment_date, status) VALUES (?, ?, ?, 'Paid')",
                          (student_id, amount, date.today()))
                conn.commit()
                st.success("Payment recorded!")

    with tab2:
        dues_df = pd.read_sql_query("""
            SELECT s.name, s.roll_no, SUM(f.amount) as total_paid
            FROM fees f JOIN students s ON f.student_id = s.id
            WHERE f.status = 'Paid'
            GROUP BY s.id
        """, conn)
        st.dataframe(dues_df) if not dues_df.empty else st.info("No payments recorded.")

# ========================
# EXAMS & RESULTS
# ========================
elif page == "📊 Exams & Results":
    st.title("📊 Exams & Results")

    if st.button("➕ Create New Exam"):
        with st.form("new_exam"):
            exam_name = st.text_input("Exam Name")
            class_name = st.text_input("Class")
            subject = st.text_input("Subject")
            max_marks = st.number_input("Max Marks", 100)
            exam_date = st.date_input("Exam Date")
            if st.form_submit_button("Create"):
                c.execute("INSERT INTO exams (exam_name, class, subject, max_marks, date) VALUES (?, ?, ?, ?, ?)",
                          (exam_name, class_name, subject, max_marks, exam_date))
                conn.commit()
                st.success("Exam created!")

    exams_df = pd.read_sql_query("SELECT * FROM exams", conn)
    st.dataframe(exams_df) if not exams_df.empty else st.info("No exams scheduled.")

# ========================
# LIBRARY
# ========================
elif page == "📚 Library":
    st.title("📚 Library Management")

    with st.expander("➕ Add New Book"):
        with st.form("add_book"):
            title = st.text_input("Title")
            author = st.text_input("Author")
            isbn = st.text_input("ISBN")
            copies = st.number_input("Copies", 1)
            if st.form_submit_button("Add Book"):
                c.execute("INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
                          (title, author, isbn, copies, copies))
                conn.commit()
                st.success("Book added!")

    books_df = pd.read_sql_query("SELECT title, author, available_copies FROM books", conn)
    st.dataframe(books_df)

# ========================
# TIMETABLE
# ========================
elif page == "🗓️ Timetable":
    st.title("🗓️ Class Timetable")
    st.info("Timetable module under development. Basic view coming soon!")

conn.close()
