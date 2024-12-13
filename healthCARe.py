import sqlite3 # For database operations
from getpass import getpass # For secure password input

#------------------Database Connection----------------------
# Connect to the SQLite database
con = sqlite3.connect('HealthCARe.db')
cur = con.cursor()

#------------------Creates database tables if they don't exists----------------------
def tables(): 
    # Create the `patients` table to store patient information
    cur.execute('''
    CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            age INTEGER,
            date_of_birth DATE,
            address TEXT,
            phone_number TEXT UNIQUE,
            password TEXT)
    ''')

    # Create the `appointments` table to store patient appointment details
    cur.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            schedule_id INTEGER,
            appointment_type TEXT,
            appointment_date DATE,
            appointment_time TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            FOREIGN KEY (schedule_id) REFERENCES admin_schedules(schedule_id))
    ''')

    # Create the `admin_schedules` table to store admin-managed schedules
    cur.execute('''
    CREATE TABLE IF NOT EXISTS admin_schedules (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_date DATE,
            schedule_time TEXT,
            capacity INTEGER)
    ''')
    con.commit()

#--------------------------------------handles patient login---------------------------------------------------
def patient_access():
    while True:  
        print("\n=============================================================")
        print("|                        PATIENT PORTAL                      |")
        print("=============================================================")
        print("[1] LOGIN")
        print("[2] SIGN UP")
        print("[3] RETURN TO MAIN MENU")
        print("-------------------------------------------------------------")

        choice = input("Enter your Choice: ").strip()

        if choice == "1":
            print("\n=============================================================")
            print("|                      PATIENT LOG IN                       |")
            print("=============================================================")
            phone_number = input("Enter your phone number: ").strip()
            password = getpass("\n  Enter your password  : ").strip()

            if not phone_number or not password:
                print("\n***** Phone number and password cannot be empty. *****\n")
                continue 

            # Validate login credentials
            cur.execute("SELECT patient_id, full_name FROM patients WHERE phone_number = ? AND password = ?", (phone_number, password))
            patient = cur.fetchone()
            print("\n+++++ Login successfully! +++++")

            if patient:
                patient_menu(patient[0], patient[1])
                return  
            else:
                print("\n***** Invalid phone number or password! Returning to Patient Menu. *****\n")
        
        elif choice == "2":
            patient_signup()
            return  
        
        elif choice == "3":
            print("\nRETURNING TO THE MAIN MENU...")
            return  

        else:
            print("\n***** Invalid choice! Please try again. *****\n")


#-----------------------------sign up for new patient-----------------------------------
def patient_signup():
    print("\n=============================================================")
    print("|                     PATIENT SIGN UP                      |")
    print("=============================================================")
    full_name = input("Enter your Full Name: ")
    while True:
        try:
            age = int(input("Enter your age: "))
            if age <= 0:
                print("\n***** Age must be a positive integer! *****\n")
                continue
            break
        except ValueError:
            print("\n***** Invalid input! Please enter a valid age. *****\n")
    
    date_of_birth = input("Enter your Date of Birth (YYYY-MM-DD): ")
    address = input("Enter your Address: ")
    phone_number = input("Enter your Phone Number: ")
    
    while True:
        # Ensure password confirmation
        password = getpass("Enter your Password: ")
        confirm_password = getpass("Confirm your Password: ")
        
        if password == confirm_password:
            break
        else:
            print("\n***** Passwords do not match! Please try again. *****\n")
    
    # Check if the phone number already exists in the database
    cur.execute("SELECT patient_id FROM patients WHERE phone_number = ?", (phone_number,))
    existing_user = cur.fetchone()

    if existing_user:
        print("\n***** [ERROR] Phone number already exists. *****\n")
    else:
        # Insert new patient into the database
        cur.execute("INSERT INTO patients (full_name, age, date_of_birth, address, phone_number, password) VALUES (?, ?, ?, ?, ?, ?)",
                    (full_name, age, date_of_birth, address, phone_number, password))
        con.commit()
        print("\n+++++ Account created successfully! +++++")
        patient_access()


#----------------------------------Display the Patient menu-----------------------------------------------
def patient_menu(patient_id, patient_name):
    while True:
        print(f"\n=============================================================")
        print(f"              WELCOME, {patient_name.upper()}              ")
        print("=============================================================")
        print("[1] Schedule Appointment")
        print("[2] View Appointments")
        print("[3] Delete Account")
        print("[4] Logout")
        print("-------------------------------------------------------------")
        
        choice = input("Enter your choice: ")

        if choice == "1":
            schedule_appointment(patient_id)
        elif choice == "2":
            view_appointments(patient_id)
        elif choice == "3":
            if delete_account(patient_id):
                return
        elif choice == "4":
            print("\nLOGGING OUT...")
            break
        else:
            print("\n***** Invalid choice! Please try again. *****\n")

#------------------------------Allow patients to schedule an appointment-------------------------------------
def schedule_appointment(patient_id):
    # Fetch only schedules with capacity > 0
    cur.execute("SELECT * FROM admin_schedules WHERE capacity > 0")
    schedules = cur.fetchall()
    
    if not schedules:
        print("\n             ***** NO AVAILABLE SCHEDULES. *****")
        return

    # Display available schedules
    print("\n==================== AVAILABLE SCHEDULES ====================")
    for idx, (schedule_id, schedule_date, schedule_time, capacity) in enumerate(schedules):
        print(f"[{idx + 1}] {schedule_date} at {schedule_time} (Remaining slots: {capacity})")

    while True:
        choice = input("Choose a schedule: ")
        
        if choice.isdigit():
            choice = int(choice)  
            if 1 <= choice <= len(schedules):
                break  
            else:
                print("\n***** Invalid choice! *****\n")
        else:
            print("\n***** Invalid input! Please enter a valid number. *****")
    
    schedule = schedules[choice - 1]
    schedule_id = schedule[0]  # Get the schedule_id
    appointment_type = input("Enter appointment type (e.g., vaccination, checkup, urgent care): ")

    # Insert the appointment and reduce schedule capacity
    cur.execute(
        "INSERT INTO appointments (patient_id, schedule_id, appointment_type, appointment_date, appointment_time) VALUES (?, ?, ?, ?, ?)",
    (patient_id, schedule_id, appointment_type, schedule[1], schedule[2])
    )
    cur.execute(
        "UPDATE admin_schedules SET capacity = capacity - 1 WHERE schedule_id = ?",
        (schedule[0],)
    )
    con.commit()

    # Automatically remove schedules with no remaining capacity
    cur.execute("DELETE FROM admin_schedules WHERE capacity <= 0")
    con.commit()

    print("\n+++++ Appointment scheduled successfully! +++++\n")


#--------------------Allow patients to view and manage their appointments---------------------------------
def view_appointments(patient_id):
    print("\n=============================================================")
    print("|                      YOUR APPOINTMENTS                    |")
    print("=============================================================")

    # Fetch appointments for the patient
    cur.execute("""
    SELECT a.appointment_id, a.appointment_type, s.schedule_date, s.schedule_time, a.status 
    FROM appointments a
    JOIN admin_schedules s ON a.schedule_id = s.schedule_id
    WHERE a.patient_id = ?
    """, (patient_id,))
    appointments = cur.fetchall()

    if not appointments:
        print("             ***** NO APPOINTMENTS FOUND *****")
        return

    # Count total number of appointments for the patient
    cur.execute("SELECT COUNT(*) FROM appointments WHERE patient_id = ?", (patient_id,))
    total_appointments = cur.fetchone()[0]

    # Display appointments
    print("\n-------------------------------------------------------------")
    for idx, (appointment_id, appointment_type, schedule_date, schedule_time, status) in enumerate(appointments):
        print(f"[{idx + 1}] {appointment_type} on {schedule_date} at {schedule_time} - {status}")
    print("-------------------------------------------------------------")

    # Display total count
    print(f"\nTotal Appointments: {total_appointments}\n")

    delete_app = input("Do you want to delete an appointment? (yes/no): ").lower()

    if delete_app == "yes":
        appointment_idx_input = input("Enter the appointment number to delete: ")
        
        if appointment_idx_input.isdigit(): 
            appointment_idx = int(appointment_idx_input)
            
            if 1 <= appointment_idx <= len(appointments):
                appointment_id = appointments[appointment_idx - 1][0]
                cur.execute("DELETE FROM appointments WHERE appointment_id = ?", (appointment_id,))
                con.commit()
                print("\n+++++ Appointment deleted successfully! +++++\n")
            else:
                print("\n***** Invalid appointment number. *****\n")
        
        else:
            print("\n***** Invalid input! Please enter a number. *****\n")
    
    elif delete_app == "no":
        print("\nRETURNING TO THE PATIENT MENU...")
    else:
        print("\n***** Invalid choice! Returning to the Patient Menu... *****\n")


#-----------------------------Allow patients to delete their account------------------------------------
def delete_account(patient_id):
    cur.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    patient = cur.fetchone() # Fetch the patient's record from the patients table
    
    if not patient:
        print("\n***** Account not found. *****\n")
        return False

    print("\n==================== YOUR DETAILS ====================")
    print(f"  Patient ID : {patient[0]}")
    print(f"  Full Name  : {patient[1]}")
    print(f"     Age     : {patient[2]}")
    print(f"Date of Birth: {patient[3]}")
    print(f"   Address   : {patient[4]}")
    print(f"Phone Number : {patient[5]}")
    print("======================================================")

    # Fetch and display the patient's appointments
    cur.execute("SELECT * FROM appointments WHERE patient_id = ?", (patient_id,))
    appointments = cur.fetchall()
    
    if appointments:
        print("\n=================== YOUR APPOINTMENTS ===================")
        for app in appointments:
            print(f"Appointment ID: {app[0]}")
            print(f"  Type  : {app[3]}")
            print(f"  Date  : {app[4]}")
            print(f"  Time  : {app[5]}")
            print("------------------------------------------------------")
    else:
        print("\n***** No appointments found. *****")

    confirmation = input("Are you sure you want to delete your account? (yes/no): ").lower()
    
    if confirmation == "yes":
        password = getpass("Enter your password: ")
        confirm_password = getpass("Confirm your password: ")

        if password == confirm_password and password == patient[6]:
            # Delete the patient's account and their appointments
            cur.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
            cur.execute("DELETE FROM appointments WHERE patient_id = ?", (patient_id,))
            con.commit()
            print("\n+++++ Account deleted successfully! +++++\n")
            return True  
        
        else:
            print("\n***** PASSWORD MISMATCH OR INCORRECT PASSWORD *****\n")
            return False  

    else:
        print("\nACCOUNT DELETION CANCELED. Returning to the previous menu...")
        return False  

#----------------------------Handle admin-related operations-----------------------------------
def admin_access():
    print("\n==================== ADMIN ====================")
    
    while True:
        admin_password = getpass("Enter admin password: ")
        
        if admin_password == "admin123":  # Replace with secure handling
            break
        else:
            print("\n***** Invalid password! Please try again. *****\n")
    
    while True:
        print("\n=============================================================")
        print("|                        ADMIN MENU                         |")
        print("=============================================================")
        print("[1] View All Patient Appointments")
        print("[2] Update Available Schedules")
        print("[3] Logout")
        print("-------------------------------------------------------------")
        
        choice = input("Enter your choice: ")

        if choice == "1":
            view_all_appointments()
        elif choice == "2":
            update_schedule()
        elif choice == "3":
            print("\nLOGGING OUT...")
            break
        else:
            print("\n***** Invalid choice! *****\n")


#-----------------------View all patient appointments-----------------------------------------------
def view_all_appointments():
    print("\n=============================================================")
    print("|                  ALL PATIENT APPOINTMENTS                 |")
    print("=============================================================")

    # Fetch all appointments with patient details
    cur.execute("""
    SELECT a.appointment_id, p.full_name, a.appointment_type, a.appointment_date, a.appointment_time, a.status 
    FROM appointments a 
    JOIN patients p ON a.patient_id = p.patient_id
    """)
    appointments = cur.fetchall()

    if not appointments:
        print("             ***** NO APPOINTMENTS FOUND *****")
        return

    # Count appointments by status
    cur.execute("SELECT status, COUNT(*) FROM appointments GROUP BY status")
    status_counts = cur.fetchall()

    print("Appointments:")
    for appointment in appointments:
        print("---------------------------------------")
        print(f"|   ID   | {appointment[0]}")
        print(f"|  Name  | {appointment[1]}")
        print(f"|  Type  | {appointment[2]}")
        print(f"|  Date  | {appointment[3]}")
        print(f"|  Time  | {appointment[4]}")
        print(f"| Status | {appointment[5]}")
        print("---------------------------------------")

    # Display totals
    print("\n-------------------- APPOINTMENT SUMMARY --------------------")
    for status, count in status_counts:
        print(f"Total {status}: {count}")
    print("-------------------------------------------------------------")

    choice = input("Do you want to mark an appointment as completed? (yes/no): ").lower()

    if choice == "yes":
        app_id = input("Enter the appointment ID: ")

        if app_id.isdigit():
            app_id = int(app_id)
            cur.execute("SELECT * FROM appointments WHERE appointment_id = ?", (app_id,))
            appointment = cur.fetchone()

            if appointment:
                # Update the appointment status to "Completed"
                cur.execute("UPDATE appointments SET status = 'COMPLETED' WHERE appointment_id = ?", (app_id,))
                con.commit()
                print("\n+++++ Appointment status updated successfully! +++++\n")
            else:
                print("\n***** No appointment found with the given ID. *****\n")
        else:
            print("\n***** Invalid input! Please enter a valid appointment ID. *****\n")

    elif choice == "no":
        print("\nRETURNING TO ADMIN MENU...")
    else:
        print("\n***** Invalid choice! Returning to Admin Menu... *****\n")

#---------------------------Update the schedule for appointments--------------------------------------
def update_schedule():
    print("\n=============================================================")
    print("|              ADMIN SCHEDULE MANAGEMENT                   |")
    print("=============================================================")
    
    # Display all admin schedules
    cur.execute("SELECT * FROM admin_schedules")
    schedules = cur.fetchall()

    if schedules:
        print("\n===================== EXISTING SCHEDULES =====================")
        for idx, (schedule_id, schedule_date, schedule_time, capacity) in enumerate(schedules):
            print(f"[{idx + 1}] {schedule_date} at {schedule_time} (Remaining slots: {capacity})")
    else:
        print("             ***** NO SCHEDULES AVAILABLE *****")

    print("\n---------------------- UPDATE SCHEDULE ----------------------")
    print("[1] Add a New Schedule")
    print("[2] Delete a Schedule")
    print("[3] Return to Admin Menu")
    print("-------------------------------------------------------------")

    choice = input("Enter your choice: ")
    
    if choice == "1":
        print("\n++++++++++++++++++++ ADD NEW SCHEDULE ++++++++++++++++++++")
        date = input("Enter date (YYYY-MM-DD): ")
        time = input("Enter time (HH:MM AM/PM): ")
        
        try:
            capacity = int(input("Enter the maximum number of appointments: "))
        except ValueError:
            print("\n***** Invalid input for capacity! Please enter a number. *****\n")
            return
        
        # Insert the new schedule into the database
        cur.execute("INSERT INTO admin_schedules (schedule_date, schedule_time, capacity) VALUES (?, ?, ?)", (date, time, capacity))
        con.commit()
        print("\n+++++ New schedule added successfully! +++++\n")

    elif choice == "2":
        if not schedules:
            print("\n***** No schedules to delete! *****\n")
            return

        print("\n==================== DELETE A SCHEDULE ====================")
        try:
            delete_choice = int(input("Enter the schedule number to delete: "))
            if 1 <= delete_choice <= len(schedules):
                schedule_id = schedules[delete_choice - 1][0]
                # Delete the selected schedule from the database
                cur.execute("DELETE FROM admin_schedules WHERE schedule_id = ?", (schedule_id,))
                con.commit()
                print("\n+++++ Schedule deleted successfully! +++++\n")
            else:
                print("\n***** Invalid schedule number. *****\n")
        
        except ValueError:
            print("\n***** Invalid input! Please enter a valid number. *****\n")

    elif choice == "3":
        print("\nRETURNING TO ADMIN MENU...")
        return
    
    else:
        print("\n***** Invalid choice! *****\n")

    # Automatically remove schedules with zero remaining capacity
    cur.execute("DELETE FROM admin_schedules WHERE capacity <= 0")
    con.commit()


#------------------------------------------------Main program loop-----------------------------------------
def healthCARe_main():
    while True:
        print("\n  -------------------------------------------------------------------")
        print("  |                                                                 |")
        print("  |   CARe: Coordinated Access for Reliable Healthcare Scheduling   |")
        print("  |                                                                 |")
        print("  -------------------------------------------------------------------\n")

        print("     \"Welcome to CARe-- your trusted partner in managing healthcare")
        print("appointments with ease and efficiency. Our system ensures seamless access,")
        print("   reliable scheduling, and coordinated care for a healthier tomorrow.\"\n")
        
        # Main menu options for user selection (patient, healthcare staff, or exit)
        print("=============================================================")
        print("        Are you a: [1] Patient | [2] Healthcare Staff")
        print("=============================================================")
        print("[3] Exit")
        print("-------------------------------------------------------------")
        choice = input("Enter your choice: ")

        if choice == "1":
            patient_access()
        elif choice == "2":
            admin_access()
        elif choice == "3":
            print("\n#############################################################")
            print("#                                                           #")
            print("#           Thank you for using CARe. Stay healthy!         #")
            print("#                                                           #")
            print("#############################################################")
            break
        else:
            print("\n*****Invalid choice! Please try again.*****\n")

tables()
healthCARe_main()