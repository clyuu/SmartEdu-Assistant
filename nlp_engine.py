import sqlite3
import re
import random
import os
from datetime import datetime

from database import DB_NAME, initialize_database


class SmartEduNLPEngine:
    def __init__(self):
        """
        Initialize the NLP engine.
        If the database is missing, it will be created automatically.
        """
        if not os.path.exists(DB_NAME):
            initialize_database()

        self.last_course = None

        # In-memory trained data
        self.training_data = []
        self.admin_answer_cache = []
        self.last_training_time = None

        self.stop_words = {
            "what", "is", "are", "the", "a", "an", "of", "for", "to", "in",
            "on", "at", "and", "or", "me", "my", "your", "you", "i", "do",
            "does", "can", "could", "would", "should", "please", "tell",
            "show", "give", "about", "here", "there", "with", "from"
        }

        self.normalization_map = {
            "fees": "fee",
            "payments": "payment",
            "paying": "pay",
            "paid": "pay",
            "courses": "course",
            "programs": "program",
            "programmes": "program",
            "degrees": "degree",
            "requirements": "requirement",
            "qualifications": "qualification",
            "years": "year",
            "months": "month",
            "scholarships": "scholarship",
            "discounts": "discount",
            "applications": "application",
            "applying": "apply",
            "applied": "apply",
            "admissions": "admission",
            "locations": "location",
            "addresses": "address",
            "emails": "email",
            "numbers": "number"
        }

        # Initial training when chatbot starts
        self.train_model()

    def get_connection(self):
        """Return database connection."""
        return sqlite3.connect(DB_NAME)

    # ---------------------------------------------------------
    # Training / Retraining
    # ---------------------------------------------------------

    def train_model(self):
        """
        Train/retrain the lightweight knowledge model.

        This is NOT neural network training.
        This process loads verified training phrases and admin-approved answers
        from SQLite into memory. New admin answers become active only after this
        method runs.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Load intent training phrases
        cursor.execute("SELECT intent_name, phrase FROM training_phrases")
        self.training_data = cursor.fetchall()

        # Load admin-approved answers into an in-memory cache
        cursor.execute("SELECT question, answer FROM admin_answers")
        self.admin_answer_cache = cursor.fetchall()

        conn.close()

        self.last_training_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def load_training_data(self):
        """
        Backward-compatible method.
        Calls train_model().
        """
        self.train_model()

    # ---------------------------------------------------------
    # NLP Preprocessing
    # ---------------------------------------------------------

    def clean_text(self, text):
        """
        Lowercase the text and remove punctuation.
        """
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text):
        """
        Split sentence into words.
        """
        return text.split()

    def normalize_word(self, word):
        """
        Convert words like fees -> fee, courses -> course.
        This is simple word normalization.
        """
        return self.normalization_map.get(word, word)

    def preprocess(self, text):
        """
        Full preprocessing:
        lowercase → remove punctuation → tokenize → remove stop words → normalize
        """
        cleaned = self.clean_text(text)
        words = self.tokenize(cleaned)

        processed_words = []
        for word in words:
            if word not in self.stop_words:
                processed_words.append(self.normalize_word(word))

        return processed_words

    # ---------------------------------------------------------
    # Similarity / Intent Matching
    # ---------------------------------------------------------

    def calculate_similarity(self, user_words, phrase_words):
        """
        Calculate similarity between user question and a training phrase.
        Uses a simple hybrid score based on common important words.
        """
        if not user_words or not phrase_words:
            return 0.0

        user_set = set(user_words)
        phrase_set = set(phrase_words)

        common_words = user_set.intersection(phrase_set)
        all_words = user_set.union(phrase_set)

        if not all_words:
            return 0.0

        jaccard_score = len(common_words) / len(all_words)
        containment_score = len(common_words) / min(len(user_set), len(phrase_set))

        final_score = (0.7 * jaccard_score) + (0.3 * containment_score)
        return final_score

    def keyword_fallback_intent(self, user_words):
        """
        If similarity score is low, use important keywords to guess the intent.
        This improves questions like 'SE fee' or 'Cyber duration'.
        """
        words = set(user_words)

        keyword_rules = {
            "course_fee": {"fee", "price", "cost", "payment", "pay", "amount"},
            "course_duration": {"duration", "long", "year", "month", "period", "time"},
            "course_requirement": {"requirement", "qualification", "need", "al", "ol", "maths", "ict"},
            "course_description": {"detail", "details", "learn", "study", "describe", "explain"},
            "course_list": {"course", "program", "degree", "available", "list"},
            "application_process": {"apply", "application", "admission", "register", "enroll", "join"},
            "scholarship": {"scholarship", "discount", "financial", "aid", "reduction"},
            "campus_location": {"location", "address", "campus", "located", "visit"},
            "contact_details": {"contact", "phone", "email", "call", "number"},
            "payment_options": {"installment", "monthly", "payment", "plan"},
            "course_availability": {"offer", "available", "provide"}
        }

        best_intent = "unknown"
        best_count = 0

        for intent, keywords in keyword_rules.items():
            count = len(words.intersection(keywords))
            if count > best_count:
                best_count = count
                best_intent = intent

        if best_count > 0:
            return best_intent, 0.55

        return "unknown", 0.0

    def detect_intent(self, user_message):
        """
        Detect the best intent using trained phrases in memory.
        """
        user_words = self.preprocess(user_message)

        best_intent = "unknown"
        best_score = 0.0

        for intent_name, phrase in self.training_data:
            phrase_words = self.preprocess(phrase)
            score = self.calculate_similarity(user_words, phrase_words)

            if score > best_score:
                best_score = score
                best_intent = intent_name

        # If training phrase matching is weak, try keyword fallback
        if best_score < 0.45:
            fallback_intent, fallback_score = self.keyword_fallback_intent(user_words)

            if fallback_score > best_score:
                best_intent = fallback_intent
                best_score = fallback_score

        return best_intent, round(best_score, 2), user_words

    # ---------------------------------------------------------
    # Course Entity Detection
    # ---------------------------------------------------------

    def get_all_courses(self):
        """
        Load all active courses and aliases directly from database.
        Course facts are dynamic knowledge base data.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT course_name, aliases
            FROM courses
            WHERE status = 'active'
        """)

        courses = cursor.fetchall()
        conn.close()
        return courses

    def alias_matches_message(self, alias, cleaned_message):
        """
        Check whether a course alias appears in the user message.
        Handles both single-word and multi-word aliases.
        """
        alias = alias.strip().lower()

        if not alias:
            return False

        if " " in alias:
            return alias in cleaned_message

        pattern = r"\b" + re.escape(alias) + r"\b"
        return re.search(pattern, cleaned_message) is not None

    def detect_course_entity(self, user_message):
        """
        Detect course name from user question using course names and aliases.
        Example:
        'SE fee' → Software Engineering
        'cybersecurity duration' → Cyber Security
        """
        cleaned_message = self.clean_text(user_message)
        courses = self.get_all_courses()

        for course_name, aliases in courses:
            possible_names = [course_name.lower()]

            if aliases:
                possible_names.extend([alias.strip().lower() for alias in aliases.split(",")])

            for name in possible_names:
                if self.alias_matches_message(name, cleaned_message):
                    self.last_course = course_name
                    return course_name

        return None

    # ---------------------------------------------------------
    # Database Answer Retrieval
    # ---------------------------------------------------------

    def get_course_list_response(self):
        """
        Return available courses.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT course_name
            FROM courses
            WHERE status = 'active'
            ORDER BY course_name
        """)

        courses = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not courses:
            return "Sorry, there are no active courses available right now."

        course_text = "\n".join([f"- {course}" for course in courses])
        return f"SmartEdu currently offers these courses:\n{course_text}"

    def get_course_details(self, course_name):
        """
        Return all details for one course.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT course_name, duration, fee, entry_requirements, description
            FROM courses
            WHERE course_name = ? AND status = 'active'
        """, (course_name,))

        course = cursor.fetchone()
        conn.close()

        return course

    def get_faq_answer(self, intent_name):
        """
        Return FAQ answer for general questions.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT answer_text
            FROM faq_answers
            WHERE intent_name = ?
        """, (intent_name,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]

        return None

    def get_small_talk_response(self, intent_name):
        """
        Return random small talk response.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT response
            FROM small_talk
            WHERE intent_name = ?
        """, (intent_name,))

        responses = [row[0] for row in cursor.fetchall()]
        conn.close()

        if responses:
            return random.choice(responses)

        return "Hello! How can I help you?"

    def find_admin_answer(self, user_message):
        """
        Search admin-approved learned answers from the in-memory trained cache.

        Important:
        - This does NOT directly read the database every time.
        - New admin answers become active only after train_model() / retrain.
        """
        if not self.admin_answer_cache:
            return None, 0.0

        user_words = self.preprocess(user_message)

        best_answer = None
        best_score = 0.0

        for question, answer in self.admin_answer_cache:
            question_words = self.preprocess(question)
            score = self.calculate_similarity(user_words, question_words)

            if score > best_score:
                best_score = score
                best_answer = answer

        if best_score >= 0.50:
            return best_answer, round(best_score, 2)

        return None, 0.0

    # ---------------------------------------------------------
    # Saving Unknown Questions and Chat History
    # ---------------------------------------------------------

    def save_unanswered_question(self, question, predicted_intent, confidence):
        """
        Save unknown or low-confidence questions for admin review.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO unanswered_questions
            (question, predicted_intent, confidence, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (question, predicted_intent, confidence, now))

        conn.commit()
        conn.close()

    def save_chat_history(self, user_message, bot_response, intent, confidence):
        """
        Save each conversation message.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO chat_history
            (user_message, bot_response, intent, confidence, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_message, bot_response, intent, confidence, now))

        conn.commit()
        conn.close()

    # ---------------------------------------------------------
    # Main Response Logic
    # ---------------------------------------------------------

    def generate_response(self, user_message):
        """
        Main chatbot response function.
        Input: user message
        Output: bot response + debug information
        """
        user_message = user_message.strip()

        if not user_message:
            return "Please type a question.", {
                "intent": "empty",
                "confidence": 0.0,
                "course": None
            }

        # First check admin-approved learned answers from trained memory cache
        admin_answer, admin_score = self.find_admin_answer(user_message)
        if admin_answer:
            self.save_chat_history(user_message, admin_answer, "admin_answer", admin_score)
            return admin_answer, {
                "intent": "admin_answer",
                "confidence": admin_score,
                "course": None
            }

        # Detect intent and course entity
        intent, confidence, user_words = self.detect_intent(user_message)
        course = self.detect_course_entity(user_message)

        # If user asks follow-up question like "What is the fee?"
        # use previous course context if available.
        if course is None and intent in [
            "course_fee",
            "course_duration",
            "course_requirement",
            "course_description"
        ]:
            course = self.last_course

        # Low confidence handling
        if confidence < 0.30:
            response = (
                "Sorry, I do not know the answer yet. "
                "I saved your question for admin review."
            )
            self.save_unanswered_question(user_message, intent, confidence)
            self.save_chat_history(user_message, response, "unknown", confidence)

            return response, {
                "intent": "unknown",
                "confidence": confidence,
                "course": course
            }

        if confidence < 0.45:
            response = (
                "I am not fully sure about that question. "
                "Could you ask it in another way? I also saved it for admin review."
            )
            self.save_unanswered_question(user_message, intent, confidence)
            self.save_chat_history(user_message, response, intent, confidence)

            return response, {
                "intent": intent,
                "confidence": confidence,
                "course": course
            }

        # Small talk handling
        if intent in ["greeting", "thanks", "goodbye"]:
            response = self.get_small_talk_response(intent)
            self.save_chat_history(user_message, response, intent, confidence)

            return response, {
                "intent": intent,
                "confidence": confidence,
                "course": course
            }

        # Course list
        if intent == "course_list":
            response = self.get_course_list_response()
            self.save_chat_history(user_message, response, intent, confidence)

            return response, {
                "intent": intent,
                "confidence": confidence,
                "course": course
            }

        # Course availability
        if intent == "course_availability":
            if course:
                response = f"Yes, SmartEdu offers {course}."
            else:
                user_words_set = set(user_words)

                # If the user is asking about an unknown course
                if "course" in user_words_set or "program" in user_words_set or "degree" in user_words_set:
                    response = (
                        "I am not sure whether SmartEdu offers that course. "
                        "I saved your question for admin review."
                    )
                else:
                    # General unknown facility/service question
                    response = (
                        "Sorry, I do not know the answer yet. "
                        "I saved your question for admin review."
                    )

                self.save_unanswered_question(user_message, intent, confidence)

            self.save_chat_history(user_message, response, intent, confidence)

            return response, {
                "intent": intent,
                "confidence": confidence,
                "course": course
            }

        # Course-specific answers
        if intent in [
            "course_fee",
            "course_duration",
            "course_requirement",
            "course_description"
        ]:
            if not course:
                response = "Which course are you asking about? Please mention the course name."
                self.save_chat_history(user_message, response, intent, confidence)

                return response, {
                    "intent": intent,
                    "confidence": confidence,
                    "course": None
                }

            course_data = self.get_course_details(course)

            if not course_data:
                response = (
                    "Sorry, I could not find that course in the knowledge base. "
                    "I saved your question for admin review."
                )
                self.save_unanswered_question(user_message, intent, confidence)
                self.save_chat_history(user_message, response, intent, confidence)

                return response, {
                    "intent": intent,
                    "confidence": confidence,
                    "course": course
                }

            course_name, duration, fee, entry_requirements, description = course_data

            if intent == "course_fee":
                response = f"The fee for {course_name} is {fee}."

            elif intent == "course_duration":
                response = f"The duration of {course_name} is {duration}."

            elif intent == "course_requirement":
                response = f"The entry requirements for {course_name} are: {entry_requirements}."

            elif intent == "course_description":
                response = f"{course_name}: {description}"

            else:
                response = "Sorry, I could not process that course question."

            self.save_chat_history(user_message, response, intent, confidence)

            return response, {
                "intent": intent,
                "confidence": confidence,
                "course": course
            }

        # General FAQ answers
        if intent in [
            "application_process",
            "scholarship",
            "campus_location",
            "contact_details",
            "payment_options"
        ]:
            response = self.get_faq_answer(intent)

            if not response:
                response = (
                    "Sorry, I do not have that information yet. "
                    "I saved your question for admin review."
                )
                self.save_unanswered_question(user_message, intent, confidence)

            self.save_chat_history(user_message, response, intent, confidence)

            return response, {
                "intent": intent,
                "confidence": confidence,
                "course": course
            }

        # Final fallback
        response = (
            "Sorry, I do not understand that question yet. "
            "I saved it for admin review."
        )
        self.save_unanswered_question(user_message, intent, confidence)
        self.save_chat_history(user_message, response, "unknown", confidence)

        return response, {
            "intent": "unknown",
            "confidence": confidence,
            "course": course
        }


# ---------------------------------------------------------
# Console Test Area
# ---------------------------------------------------------

if __name__ == "__main__":
    bot = SmartEduNLPEngine()

    print("SmartEdu Assistant NLP Engine Test")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("Student: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Bot: Goodbye!")
            break

        response, debug = bot.generate_response(user_input)

        print("Bot:", response)
        print("Debug:", debug)
        print()