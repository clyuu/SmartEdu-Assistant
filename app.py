import tkinter as tk
import tkinter.font as tkfont

from nlp_engine import SmartEduNLPEngine
from admin_panel import AdminPanel


class SmartEduChatApp:
    """Main SmartEdu chatbot window."""

    FONT_FAMILY = "Segoe UI"
    COLORS = {
        "app_bg": "#f5f8fc",
        "card": "#ffffff",
        "card_shadow": "#eaf1f8",
        "border": "#e7eef7",
        "primary": "#7cc8f7",
        "primary_dark": "#111a2f",
        "text": "#182234",
        "muted": "#7d8798",
        "muted_light": "#aab4c3",
        "bot_bubble": "#f3f8fd",
        "bot_border": "#dcecf8",
        "user_bubble": "#121c32",
        "input_bg": "#fafdff",
        "chip_bg": "#f4f8fc",
        "chip_hover": "#e9f4ff",
        "success": "#2f8b57",
        "warning": "#d97706",
    }

    QUICK_ACTIONS = [
        "What courses do you offer?",
        "What is the fee for Software Engineering?",
        "How long is Cyber Security?",
        "What are the entry requirements?",
        "How can I apply?",
        "Are scholarships available?",
        "Where is the campus?",
        "How can I contact SmartEdu?",
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("SmartEdu Assistant Chatbot")
        self.root.geometry("980x740")
        self.root.minsize(760, 620)
        self.root.configure(bg=self.COLORS["app_bg"])

        self.bot = SmartEduNLPEngine()
        self.last_debug = None
        self.messages = []
        self.placeholder_active = False
        self.placeholder_text = "Ask about courses, fees, entry requirements..."
        self.intro_text = (
            "SmartEdu course counselling, fees, duration, entry requirements, "
            "applications, scholarships, campus location, and contact details."
        )

        self.create_widgets()
        self.root.after(80, self.render_chat)
        self.root.after(120, self.user_input.focus_set)

    # ---------------------------------------------------------
    # UI Creation
    # ---------------------------------------------------------

    def create_widgets(self):
        self.fonts = {
            "title": tkfont.Font(family=self.FONT_FAMILY, size=24, weight="bold"),
            "subtitle": tkfont.Font(family=self.FONT_FAMILY, size=10),
            "card_title": tkfont.Font(family=self.FONT_FAMILY, size=13, weight="bold"),
            "body": tkfont.Font(family=self.FONT_FAMILY, size=11),
            "message": tkfont.Font(family=self.FONT_FAMILY, size=10),
            "message_bold": tkfont.Font(family=self.FONT_FAMILY, size=10, weight="bold"),
            "small": tkfont.Font(family=self.FONT_FAMILY, size=9),
            "button": tkfont.Font(family=self.FONT_FAMILY, size=9, weight="bold"),
            "send": tkfont.Font(family=self.FONT_FAMILY, size=13, weight="bold"),
        }

        shell = tk.Frame(self.root, bg=self.COLORS["app_bg"])
        shell.pack(fill=tk.BOTH, expand=True)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        header = tk.Frame(shell, bg=self.COLORS["app_bg"])
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(28, 14))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="SmartEdu AI Chat",
            font=self.fonts["title"],
            fg=self.COLORS["primary"],
            bg=self.COLORS["app_bg"],
        ).grid(row=0, column=0)

        tk.Label(
            header,
            text="University course counselling assistant",
            font=self.fonts["subtitle"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["app_bg"],
        ).grid(row=1, column=0, pady=(4, 0))

        body = tk.Frame(shell, bg=self.COLORS["app_bg"])
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 14))
        body.bind("<Configure>", self.layout_card)

        self.card_outer = tk.Frame(body, bg=self.COLORS["card_shadow"])
        self.card_outer.place(relx=0.5, rely=0, anchor="n", width=820, relheight=1)
        self.card_outer.grid_columnconfigure(0, weight=1)
        self.card_outer.grid_rowconfigure(0, weight=1)

        self.card = tk.Frame(
            self.card_outer,
            bg=self.COLORS["card"],
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
            highlightcolor=self.COLORS["border"],
        )
        self.card.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        self.create_card_header()
        self.create_chat_area()
        self.create_quick_actions()
        self.create_composer()
        self.create_status_bar()

    def layout_card(self, event):
        width = min(840, max(320, event.width - 28))
        self.card_outer.place_configure(width=width)

    def create_card_header(self):
        header = tk.Frame(self.card, bg=self.COLORS["card"])
        header.pack(fill=tk.X, padx=24, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title_block = tk.Frame(header, bg=self.COLORS["card"])
        title_block.grid(row=0, column=0, sticky="w")

        tk.Label(
            title_block,
            text="SmartEdu Assistant",
            font=self.fonts["card_title"],
            fg=self.COLORS["text"],
            bg=self.COLORS["card"],
        ).pack(anchor="w")

        online_row = tk.Frame(title_block, bg=self.COLORS["card"])
        online_row.pack(anchor="w", pady=(3, 0))
        tk.Canvas(
            online_row,
            width=8,
            height=8,
            bg=self.COLORS["card"],
            highlightthickness=0,
        ).pack(side=tk.LEFT, padx=(0, 6))
        dot_canvas = online_row.winfo_children()[0]
        dot_canvas.create_oval(1, 1, 7, 7, fill=self.COLORS["success"], outline="")

        tk.Label(
            online_row,
            text="Ready to help",
            font=self.fonts["small"],
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
        ).pack(side=tk.LEFT)

        action_row = tk.Frame(header, bg=self.COLORS["card"])
        action_row.grid(row=0, column=1, sticky="e")

        self.create_header_button(action_row, "Clear", self.clear_chat).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.create_header_button(action_row, "Retrain", self.reload_model).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.create_header_button(action_row, "Debug", self.show_last_debug).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.create_header_button(action_row, "Admin", self.open_admin_panel).pack(
            side=tk.LEFT, padx=(0, 6)
        )

    def create_chat_area(self):
        chat_shell = tk.Frame(self.card, bg=self.COLORS["card"])
        chat_shell.pack(fill=tk.BOTH, expand=True, padx=24, pady=(2, 12))
        chat_shell.grid_columnconfigure(0, weight=1)
        chat_shell.grid_rowconfigure(0, weight=1)

        self.chat_canvas = tk.Canvas(
            chat_shell,
            bg=self.COLORS["card"],
            highlightthickness=0,
            bd=0,
        )
        self.chat_canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(
            chat_shell,
            orient=tk.VERTICAL,
            command=self.chat_canvas.yview,
            width=10,
            bd=0,
            troughcolor=self.COLORS["card"],
            activebackground=self.COLORS["bot_border"],
        )
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)

        self.chat_canvas.bind("<Configure>", lambda event: self.render_chat())
        self.chat_canvas.bind("<MouseWheel>", self.on_mousewheel)

    def create_quick_actions(self):
        quick_shell = tk.Frame(self.card, bg=self.COLORS["card"])
        quick_shell.pack(fill=tk.X, padx=24, pady=(0, 8))
        quick_shell.grid_columnconfigure(0, weight=1)
        quick_shell.grid_columnconfigure(1, weight=0)

        self.quick_canvas = tk.Canvas(
            quick_shell,
            height=66,
            bg=self.COLORS["card"],
            highlightthickness=0,
            bd=0,
        )
        self.quick_canvas.grid(row=0, column=0, sticky="ew")

        self.quick_strip = tk.Frame(self.quick_canvas, bg=self.COLORS["card"])
        self.quick_window = self.quick_canvas.create_window(
            0,
            0,
            window=self.quick_strip,
            anchor="nw",
        )

        for question in self.QUICK_ACTIONS:
            button = tk.Button(
                self.quick_strip,
                text=question,
                font=self.fonts["button"],
                bg=self.COLORS["chip_bg"],
                fg=self.COLORS["text"],
                activebackground=self.COLORS["chip_hover"],
                activeforeground=self.COLORS["text"],
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                padx=12,
                pady=9,
                width=32,
                height=2,
                wraplength=230,
                justify=tk.CENTER,
                command=lambda q=question: self.send_suggested_question(q),
            )
            button.pack(side=tk.LEFT, padx=(0, 8), pady=3)
            self.add_hover(button, self.COLORS["chip_bg"], self.COLORS["chip_hover"])

        scroll_button = tk.Button(
            quick_shell,
            text="\u203a",
            font=self.fonts["send"],
            width=3,
            bg=self.COLORS["primary_dark"],
            fg="#ffffff",
            activebackground="#22304d",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self.scroll_quick_actions,
        )
        scroll_button.grid(row=0, column=1, sticky="e", padx=(8, 0), pady=3)
        self.add_hover(scroll_button, self.COLORS["primary_dark"], "#22304d")

        self.quick_strip.bind("<Configure>", self.update_quick_scroll_region)
        self.quick_canvas.bind("<Configure>", self.update_quick_scroll_region)

    def create_composer(self):
        composer = tk.Frame(self.card, bg=self.COLORS["card"])
        composer.pack(fill=tk.X, padx=24, pady=(0, 12))

        input_card = tk.Frame(
            composer,
            bg=self.COLORS["input_bg"],
            highlightthickness=1,
            highlightbackground=self.COLORS["bot_border"],
            highlightcolor=self.COLORS["primary"],
        )
        input_card.pack(fill=tk.X)
        input_card.grid_columnconfigure(0, weight=1)
        input_card.grid_columnconfigure(1, weight=0)

        self.user_input = tk.Entry(
            input_card,
            font=self.fonts["body"],
            bg=self.COLORS["input_bg"],
            fg=self.COLORS["text"],
            relief=tk.FLAT,
            bd=0,
            insertbackground=self.COLORS["primary_dark"],
        )
        self.user_input.grid(row=0, column=0, sticky="ew", padx=(18, 10), pady=16)
        self.user_input.bind("<Return>", self.send_message)
        self.user_input.bind("<FocusIn>", self.clear_placeholder)
        self.user_input.bind("<FocusOut>", self.restore_placeholder)
        self.user_input.bind("<KeyPress>", self.clear_placeholder_on_typing)
        self.user_input.bind("<Button-1>", self.clear_placeholder)

        send_button = tk.Button(
            input_card,
            text="\u2191",
            font=self.fonts["send"],
            width=3,
            bg=self.COLORS["primary_dark"],
            fg="#ffffff",
            activebackground="#22304d",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self.send_message,
        )
        send_button.grid(row=0, column=1, padx=(0, 14), pady=12)
        self.add_hover(send_button, self.COLORS["primary_dark"], "#22304d")

        self.restore_placeholder()

    def create_status_bar(self):
        status_frame = tk.Frame(self.card, bg=self.COLORS["card"])
        status_frame.pack(fill=tk.X, padx=24, pady=(0, 16))

        self.status_var = tk.StringVar(value="Status: Ready")
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=self.fonts["small"],
            anchor="w",
            fg=self.COLORS["muted"],
            bg=self.COLORS["card"],
        )
        self.status_label.pack(fill=tk.X)

    # ---------------------------------------------------------
    # UI Helpers
    # ---------------------------------------------------------

    def create_header_button(self, parent, text, command):
        button = tk.Button(
            parent,
            text=text,
            font=self.fonts["button"],
            bg=self.COLORS["chip_bg"],
            fg=self.COLORS["text"],
            activebackground=self.COLORS["chip_hover"],
            activeforeground=self.COLORS["text"],
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=7,
            command=command,
        )
        self.add_hover(button, self.COLORS["chip_bg"], self.COLORS["chip_hover"])
        return button

    def create_primary_button(self, parent, text, command):
        button = tk.Button(
            parent,
            text=text,
            font=self.fonts["button"],
            bg=self.COLORS["primary_dark"],
            fg="#ffffff",
            activebackground="#22304d",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=12,
            pady=8,
            command=command,
        )
        self.add_hover(button, self.COLORS["primary_dark"], "#22304d")
        return button

    def show_dialog(self, title, message, kind="info"):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=self.COLORS["app_bg"])
        dialog.geometry("420x260")
        dialog.minsize(360, 220)
        dialog.transient(self.root)
        dialog.grab_set()

        accent = {
            "info": self.COLORS["primary"],
            "success": self.COLORS["success"],
            "warning": self.COLORS["warning"],
            "error": "#d14343",
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
            font=self.fonts["card_title"],
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
            wraplength=350,
        ).pack(anchor="w", fill=tk.BOTH, expand=True, pady=(10, 16))

        self.create_primary_button(body, "OK", dialog.destroy).pack(anchor="e")
        dialog.wait_window()

    def add_hover(self, widget, normal_color, hover_color):
        widget.bind("<Enter>", lambda event: widget.configure(bg=hover_color))
        widget.bind("<Leave>", lambda event: widget.configure(bg=normal_color))

    def update_quick_scroll_region(self, event=None):
        if not hasattr(self, "quick_canvas"):
            return

        bounds = self.quick_canvas.bbox("all")
        if bounds:
            self.quick_canvas.configure(scrollregion=bounds)

    def scroll_quick_actions(self):
        if not hasattr(self, "quick_canvas"):
            return

        first, last = self.quick_canvas.xview()
        if last >= 0.98:
            self.quick_canvas.xview_moveto(0)
        else:
            self.quick_canvas.xview_scroll(1, "pages")

    def clear_placeholder(self, event=None):
        if self.placeholder_active:
            self.user_input.delete(0, tk.END)
            self.user_input.configure(fg=self.COLORS["text"])
            self.placeholder_active = False

    def clear_placeholder_on_typing(self, event=None):
        if not self.placeholder_active:
            return

        ignored_keys = {
            "Alt_L",
            "Alt_R",
            "Control_L",
            "Control_R",
            "Escape",
            "Return",
            "Shift_L",
            "Shift_R",
            "Tab",
        }
        if event and event.keysym in ignored_keys:
            return

        self.clear_placeholder()

    def restore_placeholder(self, event=None):
        if not self.user_input.get().strip():
            self.user_input.delete(0, tk.END)
            self.user_input.insert(0, self.placeholder_text)
            self.user_input.configure(fg=self.COLORS["muted_light"])
            self.placeholder_active = True

    def get_user_text(self):
        if self.placeholder_active or self.user_input.get() == self.placeholder_text:
            return ""
        return self.user_input.get().strip()

    def on_mousewheel(self, event):
        if event.delta:
            self.chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, fill, outline="", tags=None):
        tags = tags or ()
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        return canvas.create_polygon(
            points,
            fill=fill,
            outline=outline,
            smooth=True,
            splinesteps=16,
            tags=tags,
        )

    def draw_intro_orb(self, canvas, cx, cy):
        canvas.create_oval(cx - 54, cy - 54, cx + 54, cy + 54, fill="#fff5dd", outline="")
        canvas.create_oval(cx - 39, cy - 36, cx + 44, cy + 46, fill="#ffd483", outline="")
        canvas.create_oval(cx - 29, cy - 12, cx + 22, cy + 42, fill="#ff7747", outline="")
        canvas.create_oval(cx - 42, cy - 8, cx + 2, cy + 42, fill="#ff5d73", outline="")
        canvas.create_oval(cx - 18, cy - 21, cx + 42, cy + 21, fill="#ffad24", outline="")
        canvas.create_oval(cx - 7, cy - 7, cx + 39, cy + 34, fill="#ff6f27", outline="")

    def draw_avatar(self, canvas, x, y, sender):
        radius = 16
        if sender == "user":
            fill = self.COLORS["primary_dark"]
            text = "Y"
            text_color = "#ffffff"
        else:
            fill = "#eaf6ff"
            text = "S"
            text_color = self.COLORS["primary_dark"]

        canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline="")
        canvas.create_text(
            x,
            y,
            text=text,
            font=self.fonts["message_bold"],
            fill=text_color,
        )

    # ---------------------------------------------------------
    # Chat Display Methods
    # ---------------------------------------------------------

    def enable_chat_display(self):
        pass

    def disable_chat_display(self):
        pass

    def render_chat(self):
        if not hasattr(self, "chat_canvas"):
            return

        canvas = self.chat_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 320)
        height = max(canvas.winfo_height(), 320)

        if not self.messages:
            center_x = width / 2
            orb_y = max(110, int(height * 0.28))
            self.draw_intro_orb(canvas, center_x, orb_y)
            canvas.create_text(
                center_x,
                orb_y + 108,
                text=self.intro_text,
                width=min(500, width - 80),
                justify=tk.CENTER,
                font=self.fonts["body"],
                fill=self.COLORS["text"],
            )
            canvas.configure(scrollregion=(0, 0, width, height))
            return

        y = 18
        horizontal_pad = 18
        avatar_gap = 12
        max_message_width = min(520, int(width * 0.66))

        for sender, message in self.messages:
            is_user = sender == "user"
            temp_text = canvas.create_text(
                0,
                0,
                text=message,
                width=max_message_width,
                anchor="nw",
                font=self.fonts["message"],
            )
            bbox = canvas.bbox(temp_text) or (0, 0, max_message_width, 24)
            canvas.delete(temp_text)

            text_width = min(max_message_width, bbox[2] - bbox[0])
            text_height = bbox[3] - bbox[1]
            bubble_width = min(max_message_width + horizontal_pad * 2, max(92, text_width + 34))
            bubble_height = max(46, text_height + 26)

            if is_user:
                avatar_x = width - 30
                bubble_x = avatar_x - 16 - avatar_gap - bubble_width
                bubble_fill = self.COLORS["user_bubble"]
                bubble_outline = self.COLORS["user_bubble"]
                text_fill = "#ffffff"
            else:
                avatar_x = 30
                bubble_x = avatar_x + 16 + avatar_gap
                bubble_fill = self.COLORS["bot_bubble"]
                bubble_outline = self.COLORS["bot_border"]
                text_fill = self.COLORS["text"]

            bubble_x = max(8, bubble_x)
            avatar_y = y + 22
            self.draw_avatar(canvas, avatar_x, avatar_y, sender)
            self.draw_rounded_rect(
                canvas,
                bubble_x,
                y,
                bubble_x + bubble_width,
                y + bubble_height,
                18,
                bubble_fill,
                bubble_outline,
            )
            canvas.create_text(
                bubble_x + horizontal_pad,
                y + 13,
                text=message,
                width=bubble_width - horizontal_pad * 2,
                anchor="nw",
                font=self.fonts["message"],
                fill=text_fill,
            )

            y += bubble_height + 16

        canvas.configure(scrollregion=(0, 0, width, max(height, y + 20)))
        canvas.yview_moveto(1.0)

    def insert_user_message(self, message):
        self.messages.append(("user", message))
        self.render_chat()

    def insert_bot_message(self, message):
        self.messages.append(("bot", message))
        self.render_chat()

    def insert_system_message(self, message):
        self.messages.append(("bot", message))
        self.render_chat()

    # ---------------------------------------------------------
    # Main Chat Methods
    # ---------------------------------------------------------

    def send_message(self, event=None):
        """Send user message to NLP engine and show bot response."""
        user_message = self.get_user_text()

        if not user_message:
            self.show_dialog("Empty Message", "Please type a question first.", "warning")
            return

        self.insert_user_message(user_message)
        self.user_input.delete(0, tk.END)
        self.user_input.configure(fg=self.COLORS["text"])
        self.placeholder_active = False

        try:
            bot_response, debug = self.bot.generate_response(user_message)
            self.last_debug = debug
            self.insert_bot_message(bot_response)

            intent = debug.get("intent", "unknown")
            confidence = debug.get("confidence", 0.0)
            course = debug.get("course", None)

            if course:
                self.status_var.set(
                    f"Status: Intent = {intent} | Confidence = {confidence} | Course = {course}"
                )
            else:
                self.status_var.set(f"Status: Intent = {intent} | Confidence = {confidence}")

        except Exception as error:
            self.show_dialog("Error", f"Something went wrong:\n{error}", "error")
            self.insert_system_message("An error occurred while processing your message.")
        finally:
            self.restore_placeholder()

    def send_suggested_question(self, question):
        """Send a suggested question."""
        self.clear_placeholder()
        self.user_input.delete(0, tk.END)
        self.user_input.insert(0, question)
        self.placeholder_active = False
        self.send_message()

    def clear_chat(self):
        """Clear the chat display."""
        self.messages.clear()
        self.render_chat()
        self.status_var.set("Status: Chat cleared")
        self.restore_placeholder()

    def reload_model(self):
        """
        Retrain the lightweight knowledge model using verified data from database.
        """
        try:
            if hasattr(self.bot, "train_model"):
                self.bot.train_model()
                trained_time = getattr(self.bot, "last_training_time", "unknown time")
            else:
                self.bot.load_training_data()
                trained_time = "unknown time"

            self.insert_system_message(
                "Knowledge model retrained successfully using verified training phrases and admin-approved answers."
            )
            self.status_var.set(f"Status: Knowledge model retrained at {trained_time}")

        except Exception as error:
            self.show_dialog("Retrain Error", f"Could not retrain model:\n{error}", "error")

    def show_last_debug(self):
        """Show last detected intent, confidence, and course entity."""
        if not self.last_debug:
            self.show_dialog("Debug Info", "No debug information available yet.", "info")
            return

        intent = self.last_debug.get("intent", "unknown")
        confidence = self.last_debug.get("confidence", 0.0)
        course = self.last_debug.get("course", None)
        trained_time = getattr(self.bot, "last_training_time", "unknown")

        debug_message = (
            f"Detected Intent: {intent}\n"
            f"Confidence Score: {confidence}\n"
            f"Detected Course: {course}\n"
            f"Last Training Time: {trained_time}"
        )

        self.show_dialog("Last NLP Debug Info", debug_message, "info")

    def open_admin_panel(self):
        """Open the admin panel window."""
        AdminPanel(self.root, self.bot)


# ---------------------------------------------------------
# Run App
# ---------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartEduChatApp(root)
    root.mainloop()
