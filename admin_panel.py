import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import ttk
import tkinter.font as tkfont

from database import DB_NAME


class AdminPanel:
    """Modern admin workspace for SmartEdu Assistant."""

    FONT_FAMILY = "Segoe UI"
    COLORS = {
        "app_bg": "#f5f8fc",
        "card": "#ffffff",
        "border": "#dde8f3",
        "primary": "#7cc8f7",
        "primary_dark": "#111a2f",
        "text": "#182234",
        "muted": "#7d8798",
        "muted_light": "#aab4c3",
        "chip_bg": "#f4f8fc",
        "chip_hover": "#e9f4ff",
        "field_bg": "#fafdff",
        "table_row": "#fbfdff",
        "success": "#2f8b57",
        "warning": "#d97706",
        "danger": "#b42318",
        "error": "#d14343",
    }

    def __init__(self, parent, bot=None):
        self.parent = parent
        self.bot = bot
        self.selected_course_id = None
        self.metric_labels = {}

        self.window = tk.Toplevel(parent)
        self.window.title("SmartEdu Admin Panel")
        self.window.geometry("1180x780")
        self.window.minsize(980, 640)
        self.window.configure(bg=self.COLORS["app_bg"])

        self.ensure_runtime_tables()
        self.create_widgets()
        self.load_unanswered_questions()
        self.load_courses()
        self.load_intents()
        self.load_chat_history()
        self.refresh_dashboard_stats()

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    def get_connection(self):
        return sqlite3.connect(DB_NAME)

    def ensure_runtime_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()

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

    # ---------------------------------------------------------
    # Main UI
    # ---------------------------------------------------------

    def create_widgets(self):
        self.fonts = {
            "title": tkfont.Font(family=self.FONT_FAMILY, size=21, weight="bold"),
            "subtitle": tkfont.Font(family=self.FONT_FAMILY, size=10),
            "section": tkfont.Font(family=self.FONT_FAMILY, size=12, weight="bold"),
            "body": tkfont.Font(family=self.FONT_FAMILY, size=10),
            "small": tkfont.Font(family=self.FONT_FAMILY, size=9),
            "button": tkfont.Font(family=self.FONT_FAMILY, size=9, weight="bold"),
            "metric": tkfont.Font(family=self.FONT_FAMILY, size=18, weight="bold"),
        }

        self.setup_styles()

        shell = tk.Frame(self.window, bg=self.COLORS["app_bg"])
        shell.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(2, weight=1)

        self.create_header(shell)
        self.create_metrics(shell)
        self.create_notebook(shell)
        self.create_status_bar(shell)

    def setup_styles(self):
        self.style = ttk.Style(self.window)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure(
            "Smart.TNotebook",
            background=self.COLORS["card"],
            borderwidth=0,
            tabmargins=(10, 6, 10, 0),
        )
        self.style.configure(
            "Smart.TNotebook.Tab",
            background=self.COLORS["chip_bg"],
            foreground=self.COLORS["muted"],
            padding=(16, 9),
            borderwidth=0,
            font=(self.FONT_FAMILY, 9, "bold"),
        )
        self.style.map(
            "Smart.TNotebook.Tab",
            background=[("selected", self.COLORS["primary_dark"])],
            foreground=[("selected", "#ffffff")],
        )
        self.style.configure(
            "Smart.Treeview",
            background=self.COLORS["table_row"],
            fieldbackground=self.COLORS["table_row"],
            foreground=self.COLORS["text"],
            rowheight=30,
            borderwidth=0,
            font=(self.FONT_FAMILY, 9),
        )
        self.style.configure(
            "Smart.Treeview.Heading",
            background=self.COLORS["chip_bg"],
            foreground=self.COLORS["text"],
            relief=tk.FLAT,
            font=(self.FONT_FAMILY, 9, "bold"),
        )
        self.style.map(
            "Smart.Treeview",
            background=[("selected", "#dff0ff")],
            foreground=[("selected", self.COLORS["primary_dark"])],
        )
        self.style.configure(
            "Smart.TCombobox",
            fieldbackground=self.COLORS["field_bg"],
            background=self.COLORS["field_bg"],
            foreground=self.COLORS["text"],
            borderwidth=0,
            padding=8,
        )

    def create_header(self, parent):
        header = tk.Frame(parent, bg=self.COLORS["app_bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)

        title_block = tk.Frame(header, bg=self.COLORS["app_bg"])
        title_block.grid(row=0, column=0, sticky="w")

        tk.Label(
            title_block,
            text="SmartEdu Admin",
            font=self.fonts["title"],
            fg=self.COLORS["primary_dark"],
            bg=self.COLORS["app_bg"],
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="Knowledge, courses, unknown questions, and chat records",
            font=self.fonts["subtitle"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["app_bg"],
        ).pack(anchor="w", pady=(3, 0))

        actions = tk.Frame(header, bg=self.COLORS["app_bg"])
        actions.grid(row=0, column=1, sticky="e")
        self.create_button(actions, "Retrain", self.retrain_knowledge_model, "primary").pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.create_button(actions, "Close", self.window.destroy, "secondary").pack(side=tk.LEFT)

    def create_metrics(self, parent):
        metrics = tk.Frame(parent, bg=self.COLORS["app_bg"])
        metrics.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        for column in range(4):
            metrics.grid_columnconfigure(column, weight=1)

        self.create_metric_tile(metrics, "pending", "Pending", "0", 0)
        self.create_metric_tile(metrics, "courses", "Active courses", "0", 1)
        self.create_metric_tile(metrics, "answers", "Verified answers", "0", 2)
        self.create_metric_tile(metrics, "chats", "Chat records", "0", 3)

    def create_metric_tile(self, parent, key, label, value, column):
        tile = tk.Frame(
            parent,
            bg=self.COLORS["card"],
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
        )
        tile.grid(row=0, column=column, sticky="ew", padx=(0, 10) if column < 3 else 0)

        value_label = tk.Label(
            tile,
            text=value,
            font=self.fonts["metric"],
            fg=self.COLORS["primary_dark"],
            bg=self.COLORS["card"],
        )
        value_label.pack(anchor="w", padx=15, pady=(12, 0))
        tk.Label(
            tile,
            text=label,
            font=self.fonts["small"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
        ).pack(anchor="w", padx=15, pady=(1, 12))
        self.metric_labels[key] = value_label

    def create_notebook(self, parent):
        notebook_shell = tk.Frame(
            parent,
            bg=self.COLORS["card"],
            highlightthickness=0,
        )
        notebook_shell.grid(row=2, column=0, sticky="nsew")
        notebook_shell.grid_columnconfigure(0, weight=1)
        notebook_shell.grid_rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(notebook_shell, style="Smart.TNotebook")
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.create_unanswered_tab()
        self.create_training_tab()
        self.create_course_update_tab()
        self.create_chat_history_tab()

    def create_status_bar(self, parent):
        self.panel_status_var = tk.StringVar(value="Status: Admin panel ready")
        status = tk.Label(
            parent,
            textvariable=self.panel_status_var,
            font=self.fonts["small"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["app_bg"],
            anchor="w",
        )
        status.grid(row=3, column=0, sticky="ew", pady=(10, 0))

    # ---------------------------------------------------------
    # UI helpers
    # ---------------------------------------------------------

    def create_tab_frame(self):
        frame = tk.Frame(self.notebook, bg=self.COLORS["card"])
        return frame

    def create_panel(self, parent, padx=16, pady=16):
        panel = tk.Frame(
            parent,
            bg=self.COLORS["card"],
            highlightthickness=0,
        )
        panel.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)
        return panel

    def create_button(self, parent, text, command, kind="secondary"):
        if kind == "primary":
            bg = self.COLORS["primary_dark"]
            fg = "#ffffff"
            hover = "#22304d"
        elif kind == "danger":
            bg = "#fff2f0"
            fg = self.COLORS["danger"]
            hover = "#ffe4e0"
        else:
            bg = self.COLORS["chip_bg"]
            fg = self.COLORS["text"]
            hover = self.COLORS["chip_hover"]

        button = tk.Button(
            parent,
            text=text,
            font=self.fonts["button"],
            bg=bg,
            fg=fg,
            activebackground=hover,
            activeforeground=fg,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=12,
            pady=8,
            command=command,
        )
        button.bind("<Enter>", lambda event: button.configure(bg=hover))
        button.bind("<Leave>", lambda event: button.configure(bg=bg))
        return button

    def show_dialog(self, title, message, kind="info"):
        dialog = tk.Toplevel(self.window)
        dialog.title(title)
        dialog.configure(bg=self.COLORS["app_bg"])
        dialog.geometry("440x260")
        dialog.minsize(380, 220)
        dialog.transient(self.window)
        dialog.grab_set()

        accent = {
            "info": self.COLORS["primary"],
            "success": self.COLORS["success"],
            "warning": self.COLORS["warning"],
            "error": self.COLORS["error"],
        }.get(kind, self.COLORS["primary"])

        card = tk.Frame(
            dialog,
            bg=self.COLORS["card"],
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
        )
        card.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)
        tk.Frame(card, bg=accent, height=4).pack(fill=tk.X)

        body = tk.Frame(card, bg=self.COLORS["card"])
        body.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)
        tk.Label(
            body,
            text=title,
            font=self.fonts["section"],
            fg=self.COLORS["text"],
            bg=self.COLORS["card"],
        ).pack(anchor="w")
        tk.Label(
            body,
            text=message,
            font=self.fonts["body"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
            justify=tk.LEFT,
            wraplength=360,
        ).pack(anchor="w", fill=tk.BOTH, expand=True, pady=(10, 16))

        self.create_button(body, "OK", dialog.destroy, "primary").pack(anchor="e")
        dialog.wait_window()

    def ask_confirm(self, title, message):
        result = {"confirmed": False}
        dialog = tk.Toplevel(self.window)
        dialog.title(title)
        dialog.configure(bg=self.COLORS["app_bg"])
        dialog.geometry("440x250")
        dialog.minsize(380, 220)
        dialog.transient(self.window)
        dialog.grab_set()

        card = tk.Frame(
            dialog,
            bg=self.COLORS["card"],
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
        )
        card.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)
        tk.Frame(card, bg=self.COLORS["warning"], height=4).pack(fill=tk.X)

        body = tk.Frame(card, bg=self.COLORS["card"])
        body.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)
        tk.Label(
            body,
            text=title,
            font=self.fonts["section"],
            fg=self.COLORS["text"],
            bg=self.COLORS["card"],
        ).pack(anchor="w")
        tk.Label(
            body,
            text=message,
            font=self.fonts["body"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
            justify=tk.LEFT,
            wraplength=360,
        ).pack(anchor="w", fill=tk.BOTH, expand=True, pady=(10, 16))

        button_row = tk.Frame(body, bg=self.COLORS["card"])
        button_row.pack(fill=tk.X)
        self.create_button(button_row, "Cancel", dialog.destroy).pack(side=tk.RIGHT)

        def confirm():
            result["confirmed"] = True
            dialog.destroy()

        self.create_button(button_row, "Confirm", confirm, "primary").pack(side=tk.RIGHT, padx=(0, 8))
        dialog.wait_window()
        return result["confirmed"]

    def create_labeled_entry(self, parent, label, width=None):
        tk.Label(
            parent,
            text=label,
            font=self.fonts["small"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
        ).pack(anchor="w", pady=(6, 3))
        entry = tk.Entry(
            parent,
            font=self.fonts["body"],
            bg=self.COLORS["field_bg"],
            fg=self.COLORS["text"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
            highlightcolor=self.COLORS["primary"],
            insertbackground=self.COLORS["primary_dark"],
        )
        entry.pack(fill=tk.X, ipady=6)
        if width:
            entry.configure(width=width)
        return entry

    def create_labeled_text(self, parent, label, height):
        tk.Label(
            parent,
            text=label,
            font=self.fonts["small"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
        ).pack(anchor="w", pady=(6, 3))
        text = tk.Text(
            parent,
            height=height,
            wrap=tk.WORD,
            font=self.fonts["body"],
            bg=self.COLORS["field_bg"],
            fg=self.COLORS["text"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
            highlightcolor=self.COLORS["primary"],
            insertbackground=self.COLORS["primary_dark"],
        )
        text.pack(fill=tk.BOTH, expand=True)
        return text

    def set_status(self, text):
        if hasattr(self, "panel_status_var"):
            self.panel_status_var.set(text)

    def refresh_dashboard_stats(self):
        if not self.metric_labels:
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        queries = {
            "pending": "SELECT COUNT(*) FROM unanswered_questions WHERE status = 'pending'",
            "courses": "SELECT COUNT(*) FROM courses WHERE status = 'active'",
            "answers": "SELECT COUNT(*) FROM admin_answers",
            "chats": "SELECT COUNT(*) FROM chat_history",
        }
        values = {}
        for key, query in queries.items():
            cursor.execute(query)
            values[key] = cursor.fetchone()[0]
        conn.close()

        for key, value in values.items():
            self.metric_labels[key].config(text=str(value))

    # ---------------------------------------------------------
    # Tab 1: Unknown Questions
    # ---------------------------------------------------------

    def create_unanswered_tab(self):
        self.unanswered_tab = self.create_tab_frame()
        self.notebook.add(self.unanswered_tab, text="Questions")

        panel = self.create_panel(self.unanswered_tab)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        top = tk.Frame(panel, bg=self.COLORS["card"])
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        top.grid_columnconfigure(0, weight=1)
        tk.Label(
            top,
            text="Unknown Questions",
            font=self.fonts["section"],
            fg=self.COLORS["text"],
            bg=self.COLORS["card"],
        ).grid(row=0, column=0, sticky="w")

        action_row = tk.Frame(top, bg=self.COLORS["card"])
        action_row.grid(row=0, column=1, sticky="e")
        self.create_button(action_row, "Refresh", self.load_unanswered_questions).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.create_button(
            action_row, "Add Verified Answer", self.open_add_answer_window, "primary"
        ).pack(side=tk.LEFT, padx=(0, 8))
        self.create_button(action_row, "Ignore", self.mark_question_ignored, "danger").pack(
            side=tk.LEFT
        )

        table_frame = tk.Frame(panel, bg=self.COLORS["card"])
        table_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("id", "question", "predicted_intent", "confidence", "status", "created_at")
        self.unanswered_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
            style="Smart.Treeview",
        )
        self.configure_tree(self.unanswered_tree, columns)
        self.unanswered_tree.heading("id", text="ID")
        self.unanswered_tree.heading("question", text="Question")
        self.unanswered_tree.heading("predicted_intent", text="Intent")
        self.unanswered_tree.heading("confidence", text="Confidence")
        self.unanswered_tree.heading("status", text="Status")
        self.unanswered_tree.heading("created_at", text="Created")
        self.unanswered_tree.column("id", width=54, anchor=tk.CENTER)
        self.unanswered_tree.column("question", width=420)
        self.unanswered_tree.column("predicted_intent", width=140)
        self.unanswered_tree.column("confidence", width=95, anchor=tk.CENTER)
        self.unanswered_tree.column("status", width=95, anchor=tk.CENTER)
        self.unanswered_tree.column("created_at", width=160)

        self.unanswered_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.unanswered_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.HORIZONTAL,
            command=self.unanswered_tree.xview,
        )
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        self.unanswered_tree.configure(
            yscrollcommand=scrollbar.set,
            xscrollcommand=x_scrollbar.set,
        )

    def configure_tree(self, tree, columns):
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, minwidth=60, stretch=False)

    def load_unanswered_questions(self):
        for item in self.unanswered_tree.get_children():
            self.unanswered_tree.delete(item)

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, question, predicted_intent, confidence, status, created_at
            FROM unanswered_questions
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.unanswered_tree.insert("", tk.END, values=row)

        self.set_status(f"Status: Loaded {len(rows)} unknown questions")
        self.refresh_dashboard_stats()

    def get_selected_unanswered_question(self):
        selected = self.unanswered_tree.selection()

        if not selected:
            self.show_dialog("No Selection", "Please select a question first.", "warning")
            return None

        return self.unanswered_tree.item(selected[0], "values")

    def open_add_answer_window(self):
        selected = self.get_selected_unanswered_question()
        if not selected:
            return

        question_id = selected[0]
        question_text = selected[1]

        answer_window = tk.Toplevel(self.window)
        answer_window.title("Add Verified Answer")
        answer_window.geometry("700x500")
        answer_window.minsize(620, 430)
        answer_window.configure(bg=self.COLORS["app_bg"])

        card = tk.Frame(
            answer_window,
            bg=self.COLORS["card"],
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
        )
        card.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

        tk.Label(
            card,
            text="Add Verified Answer",
            font=self.fonts["section"],
            fg=self.COLORS["text"],
            bg=self.COLORS["card"],
        ).pack(anchor="w", padx=18, pady=(18, 6))

        form = tk.Frame(card, bg=self.COLORS["card"])
        form.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        tk.Label(
            form,
            text="Selected Question",
            font=self.fonts["small"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
        ).pack(anchor="w", pady=(4, 4))
        question_entry = tk.Text(
            form,
            height=3,
            wrap=tk.WORD,
            font=self.fonts["body"],
            bg=self.COLORS["field_bg"],
            fg=self.COLORS["text"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
            highlightcolor=self.COLORS["primary"],
        )
        question_entry.pack(fill=tk.X)
        question_entry.insert(tk.END, question_text)

        answer_text = self.create_labeled_text(form, "Verified Answer", 7)

        intent_frame = tk.Frame(form, bg=self.COLORS["card"])
        intent_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Label(
            intent_frame,
            text="Intent",
            font=self.fonts["small"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
        ).pack(side=tk.LEFT)
        intent_var = tk.StringVar(value="admin_answer")
        intent_combo = ttk.Combobox(
            intent_frame,
            textvariable=intent_var,
            values=[
                "admin_answer",
                "course_availability",
                "campus_location",
                "contact_details",
                "scholarship",
                "application_process",
            ],
            state="readonly",
            width=28,
            style="Smart.TCombobox",
        )
        intent_combo.pack(side=tk.LEFT, padx=(10, 0))

        button_row = tk.Frame(card, bg=self.COLORS["card"])
        button_row.pack(fill=tk.X, padx=18, pady=(0, 18))
        self.create_button(
            button_row,
            "Save Answer",
            lambda: self.save_verified_answer(
                answer_window, question_id, question_entry, answer_text, intent_var
            ),
            "primary",
        ).pack(side=tk.LEFT)
        self.create_button(button_row, "Cancel", answer_window.destroy).pack(side=tk.RIGHT)

    def save_verified_answer(self, answer_window, question_id, question_entry, answer_text, intent_var):
        updated_question = question_entry.get("1.0", tk.END).strip()
        answer = answer_text.get("1.0", tk.END).strip()
        intent_name = intent_var.get().strip()

        if not updated_question or not answer:
            self.show_dialog("Missing Data", "Question and answer cannot be empty.", "warning")
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT OR IGNORE INTO admin_answers
            (question, answer, intent_name, created_at)
            VALUES (?, ?, ?, ?)
        """, (updated_question, answer, intent_name, now))

        cursor.execute("""
            INSERT OR IGNORE INTO training_phrases
            (intent_name, phrase, created_at)
            VALUES (?, ?, ?)
        """, (intent_name, updated_question, now))

        cursor.execute("""
            UPDATE unanswered_questions
            SET status = 'answered'
            WHERE id = ?
        """, (question_id,))

        conn.commit()
        conn.close()

        self.load_unanswered_questions()
        self.set_status("Status: Verified answer saved. Retrain is required to activate it.")
        self.show_dialog("Saved", "Verified answer saved successfully.", "success")
        answer_window.destroy()

    def mark_question_ignored(self):
        selected = self.get_selected_unanswered_question()
        if not selected:
            return

        question_id = selected[0]
        confirm = self.ask_confirm("Confirm", "Do you want to mark this question as ignored?")
        if not confirm:
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE unanswered_questions
            SET status = 'ignored'
            WHERE id = ?
        """, (question_id,))
        conn.commit()
        conn.close()

        self.load_unanswered_questions()
        self.set_status("Status: Question marked as ignored")

    # ---------------------------------------------------------
    # Tab 2: Training Phrases
    # ---------------------------------------------------------

    def create_training_tab(self):
        self.training_tab = self.create_tab_frame()
        self.notebook.add(self.training_tab, text="Training")

        panel = self.create_panel(self.training_tab, padx=16, pady=16)
        panel.grid_columnconfigure(0, weight=1)

        content = tk.Frame(panel, bg=self.COLORS["card"])
        content.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

        tk.Label(
            content,
            text="Training Phrase",
            font=self.fonts["section"],
            fg=self.COLORS["text"],
            bg=self.COLORS["card"],
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(
            content,
            text="Intent",
            font=self.fonts["small"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
        ).pack(anchor="w", pady=(0, 4))
        self.intent_var = tk.StringVar()
        self.intent_combo = ttk.Combobox(
            content,
            textvariable=self.intent_var,
            state="readonly",
            width=44,
            style="Smart.TCombobox",
        )
        self.intent_combo.pack(anchor="w", fill=tk.X, ipady=4, pady=(0, 8))

        self.training_phrase_entry = self.create_labeled_entry(content, "Phrase")

        button_row = tk.Frame(content, bg=self.COLORS["card"])
        button_row.pack(fill=tk.X, pady=(16, 0))
        self.create_button(button_row, "Add Phrase", self.add_training_phrase, "primary").pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.create_button(button_row, "Retrain", self.retrain_knowledge_model).pack(side=tk.LEFT)

    def load_intents(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT intent_name
            FROM intents
            ORDER BY intent_name
        """)
        intents = [row[0] for row in cursor.fetchall()]
        conn.close()

        if hasattr(self, "intent_combo"):
            self.intent_combo["values"] = intents
            if intents:
                self.intent_combo.current(0)

    def add_training_phrase(self):
        intent_name = self.intent_var.get().strip()
        phrase = self.training_phrase_entry.get().strip()

        if not intent_name or not phrase:
            self.show_dialog("Missing Data", "Please select an intent and type a phrase.", "warning")
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT OR IGNORE INTO training_phrases
            (intent_name, phrase, created_at)
            VALUES (?, ?, ?)
        """, (intent_name, phrase, now))

        conn.commit()
        conn.close()

        self.training_phrase_entry.delete(0, tk.END)
        self.show_dialog("Saved", "Training phrase added successfully.", "success")
        self.set_status("Status: Training phrase saved. Retraining is required to activate it.")

    # ---------------------------------------------------------
    # Tab 3: Course Update
    # ---------------------------------------------------------

    def create_course_update_tab(self):
        self.course_tab = self.create_tab_frame()
        self.notebook.add(self.course_tab, text="Courses")

        main = tk.Frame(self.course_tab, bg=self.COLORS["card"])
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        left_panel = tk.Frame(
            main,
            bg=self.COLORS["card"],
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(1, weight=1)

        left_header = tk.Frame(left_panel, bg=self.COLORS["card"])
        left_header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        left_header.grid_columnconfigure(0, weight=1)
        tk.Label(
            left_header,
            text="Course List",
            font=self.fonts["section"],
            fg=self.COLORS["text"],
            bg=self.COLORS["card"],
        ).grid(row=0, column=0, sticky="w")
        self.create_button(left_header, "Refresh", self.load_courses).grid(row=0, column=1, sticky="e")

        table_frame = tk.Frame(left_panel, bg=self.COLORS["card"])
        table_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("id", "course_name", "duration", "fee", "status")
        self.course_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
            style="Smart.Treeview",
        )
        self.configure_tree(self.course_tree, columns)
        self.course_tree.heading("id", text="ID")
        self.course_tree.heading("course_name", text="Course")
        self.course_tree.heading("duration", text="Duration")
        self.course_tree.heading("fee", text="Fee")
        self.course_tree.heading("status", text="Status")
        self.course_tree.column("id", width=60, anchor=tk.CENTER)
        self.course_tree.column("course_name", width=240)
        self.course_tree.column("duration", width=120)
        self.course_tree.column("fee", width=170)
        self.course_tree.column("status", width=90, anchor=tk.CENTER)
        self.course_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.course_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.HORIZONTAL,
            command=self.course_tree.xview,
        )
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        self.course_tree.configure(
            yscrollcommand=scrollbar.set,
            xscrollcommand=x_scrollbar.set,
        )
        self.course_tree.bind("<<TreeviewSelect>>", self.on_course_select)

        right_panel = tk.Frame(
            main,
            bg=self.COLORS["card"],
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
        )
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)

        right_header = tk.Frame(right_panel, bg=self.COLORS["card"])
        right_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        right_header.grid_columnconfigure(0, weight=1)

        tk.Label(
            right_header,
            text="Update Course",
            font=self.fonts["section"],
            fg=self.COLORS["text"],
            bg=self.COLORS["card"],
        ).grid(row=0, column=0, sticky="w")

        right_actions = tk.Frame(right_header, bg=self.COLORS["card"])
        right_actions.grid(row=0, column=1, sticky="e")
        self.create_button(right_actions, "Update", self.update_course, "primary").pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.create_button(right_actions, "Refresh", self.load_courses).pack(side=tk.LEFT)

        form = tk.Frame(right_panel, bg=self.COLORS["card"])
        form.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        self.course_name_entry = self.create_labeled_entry(form, "Course Name")
        self.aliases_entry = self.create_labeled_entry(form, "Aliases")
        self.duration_entry = self.create_labeled_entry(form, "Duration")
        self.fee_entry = self.create_labeled_entry(form, "Fee")
        self.requirement_entry = self.create_labeled_entry(form, "Entry Requirements")
        self.description_text = self.create_labeled_text(form, "Description", 5)

        tk.Label(
            form,
            text="Status",
            font=self.fonts["small"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
        ).pack(anchor="w", pady=(9, 4))
        self.course_status_var = tk.StringVar(value="active")
        self.status_combo = ttk.Combobox(
            form,
            textvariable=self.course_status_var,
            values=["active", "inactive"],
            state="readonly",
            style="Smart.TCombobox",
        )
        self.status_combo.pack(fill=tk.X, ipady=4)

    def load_courses(self):
        if not hasattr(self, "course_tree"):
            return

        for item in self.course_tree.get_children():
            self.course_tree.delete(item)

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, course_name, duration, fee, status
            FROM courses
            ORDER BY course_name
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.course_tree.insert("", tk.END, values=row)

        self.set_status(f"Status: Loaded {len(rows)} courses")
        self.refresh_dashboard_stats()

    def on_course_select(self, event=None):
        selected = self.course_tree.selection()
        if not selected:
            return

        values = self.course_tree.item(selected[0], "values")
        course_id = values[0]

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, course_name, aliases, duration, fee, entry_requirements, description, status
            FROM courses
            WHERE id = ?
        """, (course_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        (
            self.selected_course_id,
            course_name,
            aliases,
            duration,
            fee,
            entry_requirements,
            description,
            status,
        ) = row

        self.course_name_entry.delete(0, tk.END)
        self.course_name_entry.insert(0, course_name)
        self.aliases_entry.delete(0, tk.END)
        self.aliases_entry.insert(0, aliases or "")
        self.duration_entry.delete(0, tk.END)
        self.duration_entry.insert(0, duration)
        self.fee_entry.delete(0, tk.END)
        self.fee_entry.insert(0, fee)
        self.requirement_entry.delete(0, tk.END)
        self.requirement_entry.insert(0, entry_requirements)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert(tk.END, description)
        self.course_status_var.set(status)

    def update_course(self):
        if not self.selected_course_id:
            self.show_dialog("No Course", "Please select a course first.", "warning")
            return

        course_name = self.course_name_entry.get().strip()
        aliases = self.aliases_entry.get().strip()
        duration = self.duration_entry.get().strip()
        fee = self.fee_entry.get().strip()
        requirement = self.requirement_entry.get().strip()
        description = self.description_text.get("1.0", tk.END).strip()
        status = self.course_status_var.get().strip()

        if not course_name or not duration or not fee or not requirement or not description:
            self.show_dialog("Missing Data", "Please fill all course fields.", "warning")
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE courses
            SET course_name = ?,
                aliases = ?,
                duration = ?,
                fee = ?,
                entry_requirements = ?,
                description = ?,
                status = ?
            WHERE id = ?
        """, (
            course_name,
            aliases,
            duration,
            fee,
            requirement,
            description,
            status,
            self.selected_course_id,
        ))
        conn.commit()
        conn.close()

        self.load_courses()
        self.show_dialog("Updated", "Course details updated successfully.", "success")
        self.set_status("Status: Course details updated")

    # ---------------------------------------------------------
    # Tab 4: Chat History
    # ---------------------------------------------------------

    def create_chat_history_tab(self):
        self.history_tab = self.create_tab_frame()
        self.notebook.add(self.history_tab, text="Chat History")

        panel = self.create_panel(self.history_tab)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        top = tk.Frame(panel, bg=self.COLORS["card"])
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        top.grid_columnconfigure(0, weight=1)
        tk.Label(
            top,
            text="Chat History",
            font=self.fonts["section"],
            fg=self.COLORS["text"],
            bg=self.COLORS["card"],
        ).grid(row=0, column=0, sticky="w")
        self.create_button(top, "Refresh", self.load_chat_history).grid(row=0, column=1, sticky="e")

        table_frame = tk.Frame(panel, bg=self.COLORS["card"])
        table_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("id", "user_message", "bot_response", "intent", "confidence", "created_at")
        self.history_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
            style="Smart.Treeview",
        )
        self.configure_tree(self.history_tree, columns)
        self.history_tree.heading("id", text="ID")
        self.history_tree.heading("user_message", text="User")
        self.history_tree.heading("bot_response", text="Bot")
        self.history_tree.heading("intent", text="Intent")
        self.history_tree.heading("confidence", text="Confidence")
        self.history_tree.heading("created_at", text="Created")
        self.history_tree.column("id", width=60, anchor=tk.CENTER)
        self.history_tree.column("user_message", width=310)
        self.history_tree.column("bot_response", width=520)
        self.history_tree.column("intent", width=150)
        self.history_tree.column("confidence", width=110, anchor=tk.CENTER)
        self.history_tree.column("created_at", width=180)
        self.history_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.HORIZONTAL,
            command=self.history_tree.xview,
        )
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        self.history_tree.configure(
            yscrollcommand=scrollbar.set,
            xscrollcommand=x_scrollbar.set,
        )

    def load_chat_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_message, bot_response, intent, confidence, created_at
            FROM chat_history
            ORDER BY id DESC
            LIMIT 100
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.history_tree.insert("", tk.END, values=row)

        self.set_status(f"Status: Loaded {len(rows)} chat history records")
        self.refresh_dashboard_stats()

    # ---------------------------------------------------------
    # Retrain Model
    # ---------------------------------------------------------

    def retrain_knowledge_model(self):
        if self.bot:
            try:
                if hasattr(self.bot, "train_model"):
                    self.bot.train_model()
                    trained_time = getattr(self.bot, "last_training_time", "unknown time")
                else:
                    self.bot.load_training_data()
                    trained_time = "unknown time"

                self.set_status(f"Status: Knowledge model retrained successfully at {trained_time}")
                self.show_dialog("Retrained", "Knowledge model retrained successfully.", "success")
                self.refresh_dashboard_stats()

            except Exception as error:
                self.show_dialog("Retrain Error", f"Could not retrain knowledge model:\n{error}", "error")
        else:
            self.set_status("Status: No bot instance connected")

    def reload_bot_model(self):
        self.retrain_knowledge_model()
