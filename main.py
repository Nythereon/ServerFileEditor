from tkinter import *
from tkmacosx import *
import paramiko
import os
from dotenv import load_dotenv
from commands import Commands

class ServerEditorApp:
    def __init__(self):
        self.root = Tk()
        self.root.title("Server File Editor")
        self.root.config(padx=25, pady=25)

        self.commands = Commands(self)

        self.commands.center_window(self.root, 800, 400)

        # ==========================================
        # 1. TOP LOGIN BAR (Using its own frame)
        # ==========================================
        top_frame = Frame(self.root)
        top_frame.pack(anchor="n", pady=(0, 20))  # Pack at the top, add bottom margin

        user_label = Label(top_frame, text="Username:")
        user_label.grid(row=0, column=0, padx=5)

        self.user_text = Entry(top_frame, width=15, bg="white", fg="black", insertbackground="black")
        self.user_text.grid(row=0, column=1, padx=5)
        self.user_text.focus_set()

        password_label = Label(top_frame, text="Password:")
        password_label.grid(row=0, column=2, padx=5)

        self.password_text = Entry(top_frame, width=15, bg="white", fg="black", insertbackground="black")  # Hides password text
        self.password_text.grid(row=0, column=3, padx=5)

        self.login_button = Button(top_frame, text="Login", command=self.commands.login)
        self.login_button.grid(row=0, column=4, padx=5)

        ### BOTTOM FRAME ###
        bottom_frame = Frame(self.root)
        bottom_frame.pack(side="bottom")

        self.message_label = Label(bottom_frame)
        self.message_label.grid(row=0, column=0, pady=(10, 0))

        # ==========================================
        # 2. MAIN APP BODY (Using its own frame)
        # ==========================================
        main_frame = Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        # --- COLUMN 0: LEFT SIDE BUTTONS ---
        # We group these inside a tiny sub-frame so they stack perfectly without affecting row heights outside
        left_buttons_frame = Frame(main_frame)
        left_buttons_frame.grid(row=0, column=0, sticky="n", padx=(0, 15))

        self.genre_buttons = {}

        categories = ["Movies", "Kids Movies", "TV Shows", "Kids Shows", "Musicals", "Marvel", "Anime Movies",
                      "Anime"]

        for i, cat in enumerate(categories):

            # Default 'Movies' to active, others normal
            initial_state = "active" if cat == "Movies" else "normal"

            # Use lambda to pass the specific category string
            btn = Button(
                left_buttons_frame,
                text=cat,
                width=110,
                state=initial_state,
                command=lambda c=cat: self.commands.change_genre(c)
            )
            btn.grid(row=i, column=0, pady=4)

            # Store the button in our dictionary using the genre name as the key
            self.genre_buttons[cat] = btn

        # Keep track of the currently active genre name as a plain string
        self.active_genre = "Movies"

        self.display_frame = Frame(main_frame, background="white")
        self.display_frame.grid(row=0, column=1, sticky="nsew", padx=10)

        # Configure main_frame rows/columns so column 1 auto-stretches with the window
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # --- COLUMN 2: RIGHT SIDE BUTTONS ---
        right_buttons_frame = Frame(main_frame)
        right_buttons_frame.grid(row=0, column=2, sticky="n", padx=(15, 0))

        self.action_button = {}

        action_categories = ["Move", "Rename", "Delete", "Delete All"]

        for i, act in enumerate(action_categories):

            state = "disabled"

            action_buttons = Button(
                right_buttons_frame,
                text=act,
                width=110,
                state=state,
                command=lambda a=act: self.commands.action_command(a)
            )
            action_buttons.grid(row=i, column=0, pady=4)

            self.action_button[act] = action_buttons

        self.root.protocol("WM_DELETE_WINDOW", self.commands.close)
        self.root.mainloop()

if __name__ == "__main__":
    app = ServerEditorApp()
