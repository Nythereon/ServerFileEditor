import os
import time
from tkinter import Listbox, END, Scrollbar, messagebox, simpledialog, Toplevel, Label, Button

import paramiko
from typing import TYPE_CHECKING
from dotenv import load_dotenv

load_dotenv()
UNRAID_ADDRESS = os.environ.get("UNRAID_ADDRESS")


# 1. This block ONLY runs inside PyCharm for your auto-complete dropdown
if TYPE_CHECKING:
    from main import ServerEditorApp, UNRAID_ADDRESS


class Commands:
    def __init__(self, gui_instance: ServerEditorApp):
        self.gui = gui_instance


    def login(self):

        entered_username = self.gui.user_text.get()
        entered_password = self.gui.password_text.get()

        try:

            # Initialize the SSH client
            self.ssh = paramiko.SSHClient()

            # Automatically add the server's SSH key if it's the first time connecting
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the Unraid Server
            self.send_message(f"Connecting to {UNRAID_ADDRESS}...")
            self.ssh.connect(hostname=UNRAID_ADDRESS, username=entered_username, password=entered_password, timeout=10)

            # Open the SFTP subsystem
            self.sftp = self.ssh.open_sftp()
            if self.sftp:
                self.send_message("Connected successfully via SFTP!")
                self.load_movies(self.gui.active_genre)


        except Exception as e:
            self.send_message(f"Error: {e}")


    def load_movies(self, movie_category: str):
        directory = f"/mnt/user/Media/{movie_category}/"

        try:
            # Check if connected
            if not hasattr(self, 'sftp') or self.sftp is None:
                self.pause_and_refresh("Please login first!", 2)
                return

            # Clear out any old lists/scrollbars before drawing a new one
            for widget in self.gui.display_frame.winfo_children():
                widget.destroy()

            file_list = sorted(self.sftp.listdir(directory))

            scrollbar = Scrollbar(self.gui.display_frame)
            scrollbar.pack(side="right", fill="y")

            self.movie_listbox = Listbox(
                self.gui.display_frame,
                bg="white",
                fg="black"
            )

            self.movie_listbox.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=self.movie_listbox.yview)

            self.movie_listbox.bind("<<ListboxSelect>>", self.on_file_selected)

            for item in file_list:
                if item != ".DS_Store":
                    self.movie_listbox.insert(END, item)

            self.activate_button("Delete All")
            self.send_message(f"Loaded {len(file_list)} files.")


        except Exception as e:
            self.send_message(f"Error loading path: {e}")


    def close(self):
        try:
            if hasattr(self, 'sftp') and self.sftp is not None:
                self.sftp.close()

            if hasattr(self, 'ssh') and self.ssh is not None:
                self.ssh.close()

            print("SFTP and SSH connections disconnected safely.")

        except Exception as e:
            print(f"Error during disconnect: {e}")

        finally:
            # 3. CRITICAL: Destroy the Tkinter window to actually exit the program
            self.gui.root.destroy()


    def change_genre(self, clicked_genre):
        # Update tracking variable
        self.gui.active_genre = clicked_genre

        # Reset all buttons to normal, and set the clicked one to active
        for name, button_object in self.gui.genre_buttons.items():
            if name == clicked_genre:
                button_object.config(state="active")
            else:
                button_object.config(state="normal")
        else:
            self.disable_button("Move", "Rename", "Delete")

        # Tell the commands file to load the files for this specific genre!
        self.load_movies(clicked_genre)


    ### Action Command Menu ###

    def action_command(self, clicked_action):
            try:
                if clicked_action == "Move":
                    self.move_popup(self.get_path())
                elif clicked_action == "Rename":
                    self.rename(self.get_path())
                elif clicked_action == "Delete":
                    self.delete(self.get_path())
                elif clicked_action == "Delete All":
                    self.delete_all()
                elif clicked_action == "Close":
                    self.close()

            except Exception as e:
                self.send_message(f"Error: {e}")


    ### Action Button Functions ###

    def move_popup(self, current_path):
        popup = Toplevel(self.gui.root)
        popup.title("Move Destination")
        self.center_window(popup, 300, 330)


        popup.grab_set()
        Label(popup, text="Select destination genre:", font=("Arial", 12)).pack(pady=15)

        categories = ["Movies", "Kids Movies", "TV Shows", "Kids Shows", "Musicals", "Marvel", "Anime Movies", "Anime"]

        for cat in categories:
            if cat == self.gui.active_genre:
                continue

            btn = Button(
                popup,
                text=cat,
                command=lambda target_cat=cat: [self.move(current_path, target_cat), popup.destroy()]
            )
            btn.pack(pady=4, fill="x", padx=30)


    def move(self, current_path, target_genre):

        try:
            filename = os.path.basename(current_path)

            new_path = f"/mnt/user/Media/{target_genre}/{filename}"

            self.sftp.rename(current_path, new_path)
            self.disable_button("Move", "Rename", "Delete")
            self.load_movies(self.gui.active_genre)
            self.send_message(f"Moved {filename} to {target_genre}.")


        except Exception as e:
            self.send_message(f"Move Failed: {e}")


    def rename(self, path):
        old_name = os.path.basename(path)
        directory_path = os.path.dirname(path)

        if old_name:
            new_name = simpledialog.askstring(
                title="Rename File",
                prompt=f"Enter a new name for {old_name}"
            )

            if new_name:
                self.sftp.rename(path, f"{directory_path}/{new_name}")
                self.disable_button("Move", "Rename", "Delete")
                self.load_movies(self.gui.active_genre)
                self.send_message("Rename Successful.")


    def delete(self, path):
        filename = os.path.basename(path)
        if filename:
            self.sftp.remove(path)
            self.disable_button("Move", "Rename", "Delete")
            self.load_movies(self.gui.active_genre)
            self.send_message(f"Deleted {filename}")


    def delete_all(self):
        warning = messagebox.askyesno(
            title="WARNING",
            message="Are you absolutely sure? This will erase all files in this category",
            icon="warning"
        )

        if warning:
            target_directory = f"/mnt/user/Media/{self.gui.active_genre}/"

            try:
                all_files = self.sftp.listdir(target_directory)

                for file in all_files:
                    file_path = f"{target_directory}{file}"
                    self.sftp.remove(file_path)
                    self.send_message(f"Removed {len(all_files)} files from {self.gui.active_genre}.")

            except Exception as e:
                self.send_message(f"Error: {e}")

        else:
            self.send_message("Cancelled Full Deletion.")


    ### Personal Functions ###
    def send_message(self, message):
        self.gui.message_label.config(text=message)

    def pause_and_refresh(self, message:str, seconds: float):
        self.gui.message_label.config(text=message)
        self.gui.root.update()
        time.sleep(seconds)
        self.gui.message_label.config(text="")

    def activate_button(self, *button_names):
        for action_name, button_object in self.gui.action_button.items():
            if action_name in button_names:
                button_object.config(state="normal")

    def disable_button(self, *button_names):
        for action_name, button_object in self.gui.action_button.items():
            if action_name in button_names:
                button_object.config(state="disabled")

    def get_path(self):
        selected_tuple = self.movie_listbox.curselection()

        if selected_tuple:
            chosen_index = selected_tuple[0]

            filename = self.movie_listbox.get(chosen_index)

            full_path = f"/mnt/user/Media/{self.gui.active_genre}/{filename}"

            return full_path

        else: return None

    def on_file_selected(self, event):
        if self.movie_listbox.curselection():
            for action_name, button_object in self.gui.action_button.items():
                self.activate_button("Move", "Rename", "Delete")
                self.disable_button("Delete All")

    def center_window(self, window_object, width: int, height: int):

        screen_width = window_object.winfo_screenwidth()
        screen_height = window_object.winfo_screenheight()

        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))

        window_object.geometry(f"{width}x{height}+{x}+{y}")



