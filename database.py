import sqlite3
from datetime import datetime

DB_NAME = "smartedu.db"


def get_connection():
    """Create and return a database connection."""
    return sqlite3.connect(DB_NAME)


def create_tables():
    """Create all required database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Course details table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL UNIQUE,
            aliases TEXT,
            duration TEXT NOT NULL,
            fee TEXT NOT NULL,
            entry_requirements TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        )
    """)

    # Intent list table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent_name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)

    # Training phrase table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_phrases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent_name TEXT NOT NULL,
            phrase TEXT NOT NULL,
            created_at TEXT,
            UNIQUE(intent_name, phrase)
        )
    """)

    # General FAQ answer table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faq_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent_name TEXT NOT NULL UNIQUE,
            answer_text TEXT NOT NULL
        )
    """)

    # Small talk response table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS small_talk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent_name TEXT NOT NULL,
            response TEXT NOT NULL,
            UNIQUE(intent_name, response)
        )
    """)

    # Unknown questions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unanswered_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            predicted_intent TEXT,
            confidence REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)

    # Admin verified answer table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            intent_name TEXT DEFAULT 'admin_answer',
            created_at TEXT,
            UNIQUE(question, answer)
        )
    """)

    # Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            intent TEXT,
            confidence REAL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def seed_courses():
    """Insert fictional SmartEdu course data."""
    conn = get_connection()
    cursor = conn.cursor()

    courses = [
        (
            "Software Engineering",
            "software engineering,se,software degree,software",
            "3 years",
            "Rs. 250,000/year",
            "A/L or equivalent qualification",
            "Software Engineering focuses on programming, software design, databases, web development, and software project management."
        ),
        (
            "Cyber Security",
            "cyber security,cybersecurity,cyber,security",
            "3 years",
            "Rs. 270,000/year",
            "A/L ICT/Maths preferred",
            "Cyber Security focuses on network security, ethical hacking, digital forensics, and information protection."
        ),
        (
            "Data Science",
            "data science,data analytics,data,analytics",
            "3 years",
            "Rs. 280,000/year",
            "A/L or equivalent with Maths/ICT preferred",
            "Data Science focuses on data analysis, statistics, machine learning, and data visualization."
        ),
        (
            "Business Management",
            "business management,business,bm,management",
            "3 years",
            "Rs. 220,000/year",
            "A/L or equivalent qualification",
            "Business Management focuses on management, marketing, finance, entrepreneurship, and business strategy."
        ),
        (
            "Computing",
            "computing,it,information technology,computer studies",
            "2 years",
            "Rs. 180,000/year",
            "O/L + Foundation or A/L",
            "Computing focuses on IT fundamentals, programming, networking, database systems, and web technologies."
        ),
        (
            "Network Engineering",
            "network engineering,networking,network,networks",
            "3 years",
            "Rs. 240,000/year",
            "A/L or equivalent qualification",
            "Network Engineering focuses on computer networks, routing, switching, network security, and server administration."
        ),
        (
            "Digital Marketing",
            "digital marketing,marketing,online marketing",
            "1 year",
            "Rs. 120,000/year",
            "O/L or equivalent qualification",
            "Digital Marketing focuses on social media marketing, SEO, content marketing, online advertising, and analytics."
        ),
        (
            "Foundation in IT",
            "foundation in it,foundation,it foundation,foundation course",
            "1 year",
            "Rs. 150,000/year",
            "O/L or equivalent qualification",
            "Foundation in IT prepares students for higher studies in computing, software engineering, and information technology."
        )
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO courses
        (course_name, aliases, duration, fee, entry_requirements, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, courses)

    conn.commit()
    conn.close()


def seed_intents():
    """Insert chatbot intents."""
    conn = get_connection()
    cursor = conn.cursor()

    intents = [
        ("greeting", "User greets the chatbot"),
        ("thanks", "User thanks the chatbot"),
        ("goodbye", "User ends the conversation"),
        ("course_list", "User asks for available courses"),
        ("course_fee", "User asks for course fees"),
        ("course_duration", "User asks for course duration"),
        ("course_requirement", "User asks for entry requirements"),
        ("course_description", "User asks for course details or description"),
        ("application_process", "User asks how to apply"),
        ("scholarship", "User asks about scholarships or discounts"),
        ("campus_location", "User asks campus location"),
        ("contact_details", "User asks contact information"),
        ("course_availability", "User asks whether a course is available"),
        ("payment_options", "User asks about payment plans"),
        ("admin_answer", "Admin approved learned answer"),
        ("unknown", "Question not understood by the chatbot")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO intents (intent_name, description)
        VALUES (?, ?)
    """, intents)

    conn.commit()
    conn.close()


def seed_training_phrases():
    """Insert initial training phrases for NLP intent matching."""
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    phrases = [
        # Greeting
        ("greeting", "Hello", now),
        ("greeting", "Hi", now),
        ("greeting", "Hey", now),
        ("greeting", "Good morning", now),
        ("greeting", "Good afternoon", now),
        ("greeting", "Good evening", now),
        ("greeting", "Good night", now),
        ("greeting", "How are you", now),
        ("greeting", "Are you there", now),
        ("greeting", "Can you help me", now),

        # Thanks
        ("thanks", "Thank you", now),
        ("thanks", "Thanks", now),
        ("thanks", "Thanks a lot", now),
        ("thanks", "That helped me", now),
        ("thanks", "I appreciate your help", now),
        ("thanks", "Thank you very much", now),
        ("thanks", "Great help", now),
        ("thanks", "That is useful", now),

        # Goodbye
        ("goodbye", "Bye", now),
        ("goodbye", "Goodbye", now),
        ("goodbye", "See you later", now),
        ("goodbye", "I will come back later", now),
        ("goodbye", "Exit", now),
        ("goodbye", "Close", now),
        ("goodbye", "Talk to you later", now),

        # Course list
        ("course_list", "What courses do you offer", now),
        ("course_list", "Show me available courses", now),
        ("course_list", "What can I study here", now),
        ("course_list", "Tell me your degree programs", now),
        ("course_list", "List all courses", now),
        ("course_list", "Available courses", now),
        ("course_list", "What programs are available", now),
        ("course_list", "What are the courses in SmartEdu", now),
        ("course_list", "Do you have IT courses", now),
        ("course_list", "Show all study programs", now),

        # Course fee
        ("course_fee", "What is the fee for Software Engineering", now),
        ("course_fee", "How much is Cyber Security", now),
        ("course_fee", "Tell me the course fee", now),
        ("course_fee", "Data Science payment details", now),
        ("course_fee", "What is the price of the course", now),
        ("course_fee", "How much should I pay", now),
        ("course_fee", "What is the fee", now),
        ("course_fee", "Course fee details", now),
        ("course_fee", "How much is Software Engineering course", now),
        ("course_fee", "What is the annual fee", now),

        # Course duration
        ("course_duration", "How long is Computing", now),
        ("course_duration", "What is the duration", now),
        ("course_duration", "How many years is Software Engineering", now),
        ("course_duration", "Course duration details", now),
        ("course_duration", "How long does the course take", now),
        ("course_duration", "How many months is Digital Marketing", now),
        ("course_duration", "Duration of Cyber Security", now),
        ("course_duration", "How long should I study", now),
        ("course_duration", "What is the study period", now),

        # Entry requirements
        ("course_requirement", "What are the entry requirements", now),
        ("course_requirement", "Do I need A/L", now),
        ("course_requirement", "Requirements for Cyber Security", now),
        ("course_requirement", "What qualifications do I need", now),
        ("course_requirement", "Can I join after O/L", now),
        ("course_requirement", "Entry qualification for Software Engineering", now),
        ("course_requirement", "Do I need Maths", now),
        ("course_requirement", "Can I apply with O/L", now),
        ("course_requirement", "Minimum qualification", now),

        # Course description
        ("course_description", "Tell me about Software Engineering", now),
        ("course_description", "What is Cyber Security about", now),
        ("course_description", "Explain Data Science course", now),
        ("course_description", "Give me course details", now),
        ("course_description", "What will I learn in Computing", now),
        ("course_description", "Describe Business Management", now),
        ("course_description", "What is Network Engineering", now),

        # Application process
        ("application_process", "How can I apply", now),
        ("application_process", "Tell me the admission process", now),
        ("application_process", "Can I apply online", now),
        ("application_process", "How to register for a course", now),
        ("application_process", "How do I join SmartEdu", now),
        ("application_process", "What is the application process", now),
        ("application_process", "How can I enroll", now),

        # Scholarship
        ("scholarship", "Are scholarships available", now),
        ("scholarship", "Do you offer discounts", now),
        ("scholarship", "Can I get financial aid", now),
        ("scholarship", "Do you have scholarship programs", now),
        ("scholarship", "Any discount for students", now),
        ("scholarship", "Can I get a fee reduction", now),

        # Campus location
        ("campus_location", "Where is the campus", now),
        ("campus_location", "What is your location", now),
        ("campus_location", "Where is SmartEdu located", now),
        ("campus_location", "Campus address", now),
        ("campus_location", "Where can I visit SmartEdu", now),
        ("campus_location", "Is your campus in Colombo", now),

        # Contact details
        ("contact_details", "How can I contact you", now),
        ("contact_details", "What is your phone number", now),
        ("contact_details", "Give me the email address", now),
        ("contact_details", "Contact details", now),
        ("contact_details", "How do I call SmartEdu", now),
        ("contact_details", "What is your email", now),

        # Course availability
        ("course_availability", "Do you offer Software Engineering", now),
        ("course_availability", "Is Cyber Security available", now),
        ("course_availability", "Do you have Data Science course", now),
        ("course_availability", "Can I study Digital Marketing", now),
        ("course_availability", "Is Network Engineering offered", now),
        ("course_availability", "Do you provide Foundation in IT", now),

        # Payment options
        ("payment_options", "Can I pay in installments", now),
        ("payment_options", "Do you have payment plans", now),
        ("payment_options", "Can I pay monthly", now),
        ("payment_options", "What are the payment options", now),
        ("payment_options", "Do I need to pay full amount", now),
        ("payment_options", "Installment payment details", now),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO training_phrases
        (intent_name, phrase, created_at)
        VALUES (?, ?, ?)
    """, phrases)

    conn.commit()
    conn.close()


def seed_faq_answers():
    """Insert FAQ answers for general intents."""
    conn = get_connection()
    cursor = conn.cursor()

    answers = [
        (
            "application_process",
            "You can apply by filling the online application form, submitting your education certificates, and contacting the admissions team."
        ),
        (
            "scholarship",
            "SmartEdu offers limited scholarships and discounts based on academic performance and special promotions."
        ),
        (
            "campus_location",
            "SmartEdu main campus is located in Colombo. This is fictional sample data for the assignment prototype."
        ),
        (
            "contact_details",
            "You can contact SmartEdu by phone: 011-1234567 or email: info@smartedu.lk."
        ),
        (
            "payment_options",
            "Students can pay course fees annually or using installment plans, depending on the course."
        )
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO faq_answers
        (intent_name, answer_text)
        VALUES (?, ?)
    """, answers)

    conn.commit()
    conn.close()


def seed_small_talk():
    """Insert small talk responses."""
    conn = get_connection()
    cursor = conn.cursor()

    responses = [
        # Greeting responses — neutral, so they work for hi/good morning/good afternoon/good evening
        ("greeting", "Hello! I am SmartEdu Assistant. How can I help you today?"),
        ("greeting", "Hi! You can ask me about courses, fees, duration, entry requirements, or applications."),
        ("greeting", "Welcome to SmartEdu Assistant. How can I support your course enquiry?"),
        ("greeting", "Hello! I am here to help you with SmartEdu course information."),

        # Thanks responses
        ("thanks", "You are welcome!"),
        ("thanks", "Glad I could help."),
        ("thanks", "No problem. Ask me anytime about SmartEdu courses."),
        ("thanks", "Happy to help you!"),

        # Goodbye responses
        ("goodbye", "Goodbye! Have a nice day."),
        ("goodbye", "See you again soon!"),
        ("goodbye", "Thank you for using SmartEdu Assistant."),
        ("goodbye", "Bye! Feel free to come back if you need more course information.")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO small_talk
        (intent_name, response)
        VALUES (?, ?)
    """, responses)

    conn.commit()
    conn.close()


def initialize_database():
    """Create tables and insert all seed data."""
    create_tables()
    seed_courses()
    seed_intents()
    seed_training_phrases()
    seed_faq_answers()
    seed_small_talk()
    print("SmartEdu database created and seeded successfully!")


if __name__ == "__main__":
    initialize_database()