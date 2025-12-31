import streamlit as st
import sqlite3
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="School Management System",
    page_icon="🏫",
    layout="centered"
)

# Title
st.title("🏫 School Management System")
st.markdown("---")

# Database Connection
conn = sqlite3.connect("school.db", check_same_thread=False)
c = conn.cursor()

# Create Table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_no TEXT NOT NULL UNIQUE,
        class TEXT,
        section TEXT,
        age INTEGER,
        phone TEXT
    )
''')
conn.commit()

# Sidebar - Add New Student
with st.sidebar:
    st.header("➕ Add New Student")
    with st.form("add_student_form"):
        name = st.text_input("Full Name *")
        roll_no = st.text_input("Roll No *").upper()
        class_name = st.text_input("Class (e.g., 10th)")
        section = st.text_input("Section (e.g., A)").upper()
        age = st.number_input("Age", min_value=5, max_value=25, step=1)
        phone = st.text_input("Phone Number")

        submitted = st.form_submit_button("Add Student")
        if submitted:
            if name.strip() and roll_no.strip():
                try:
                    c.execute(
                        "INSERT INTO students (name, roll_no, class, section, age, phone) VALUES (?, ?, ?, ?, ?, ?)",
                        (name.strip(), roll_no.strip(), class_name.strip(), section.strip(), age, phone.strip())
                    )
                    conn.commit()
                    st.success(f"✅ {name} added successfully!")
                except sqlite3.IntegrityError:
                    st.error("❌ Roll No already exists!")
            else:
                st.warning("⚠️ Name and Roll No are required!")

# Main Area - Search & Display
st.subheader("🔍 Search Students")
search_term = st.text_input("", placeholder="Type Name or Roll No to search...")

query = "SELECT id, name, roll_no, class, section, age, phone FROM students"
params = ()

if search_term:
    search_like = f"%{search_term}%"
    query += " WHERE name LIKE ? OR roll_no LIKE ?"
    params = (search_like, search_like)

# Fetch data
df = pd.read_sql_query(query, conn, params=params)

st.subheader(f"📋 Student Records ({len(df)} students)")

if not df.empty:
    # Display editable table
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "name": "Name",
            "roll_no": "Roll No",
            "class": "Class",
            "section": "Section",
            "age": st.column_config.NumberColumn("Age", min_value=5, max_value=25),
            "phone": "Phone"
        }
    )

    # Delete selected row
    selected_rows = st.session_state.get("data_editor")  # Streamlit tracks edits
    if st.button("🗑️ Delete Selected Student", type="primary"):
        if "selected_index" in st.session_state and st.session_state.selected_index is not None:
            student_id = df.iloc[st.session_state.selected_index]["id"]
            student_name = df.iloc[st.session_state.selected_index]["name"]
            c.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()
            st.success(f"🗑️ {student_name} deleted!")
            st.rerun()
        else:
            st.warning("Please select a row first (click on it in the table).")
else:
    st.info("No students found. Add one from the sidebar!")

# Close connection
conn.close()

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Streamlit | Data saved locally in school.db")
