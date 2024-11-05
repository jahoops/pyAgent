import tkinter as tk
import schedule
import time
import threading
import webbrowser
import subprocess
import json
from datetime import datetime
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from win10toast import ToastNotifier

# Load reminders from the file
try:
    with open('reminders.json', 'r') as file:
        reminders = json.load(file)
        print("Reminders loaded successfully.")
        # Initialize the completed key for each reminder
        for reminder in reminders:
            reminder["completed"] = False
except json.JSONDecodeError as e:
    print(f"Error loading reminders: {e}")
    reminders = []

running = True
toaster = ToastNotifier()
root = None

def create_image():
    # Generate an image and draw a pattern
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), (255, 255, 255))
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=(255, 0, 0))
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=(0, 255, 0))
    dc.rectangle(
        (width // 2, height // 2, width, height),
        fill=(0, 0, 255))
    dc.rectangle(
        (0, 0, width // 2, height // 2),
        fill=(255, 255, 0))
    return image

def open_website(reminder):
    if "url" in reminder and reminder["url"]:
        try:
            print(f"Opening website for {reminder['name']}")
            edge_path = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
            subprocess.Popen([edge_path, reminder["url"]])
        except Exception as e:
            print(f"Error opening website: {e}")
    else:
        print(f"No URL provided for {reminder['name']}")

def mark_task_done(reminder, button):
    reminder["completed"] = True
    print(f"Task marked as done for {reminder['name']}")
    button.config(text="Already Done", state=tk.DISABLED)

def remind_and_open_website(reminder):
    if not reminder["completed"]:
        print(f"Showing reminder notification for {reminder['name']}")
        toaster.show_toast(
            reminder["name"],
            f"Reminder: {reminder['name']}",
            duration=10,
            threaded=True
        )
        # Schedule the next check in 60 seconds
        schedule.every(1).minutes.do(check_reminder, reminder)

def check_reminder(reminder):
    if not reminder["completed"]:
        remind_and_open_website(reminder)
    return schedule.CancelJob

def reset_task_flags():
    for reminder in reminders:
        reminder["completed"] = False

def setup_schedule():
    for reminder in reminders:
        for day in reminder["days"]:
            print(f"Scheduling {reminder['name']} on {day} at {reminder['time']}")
            getattr(schedule.every(), day).at(reminder["time"]).do(remind_and_open_website, reminder)

    # Schedule the tasks to remind every hour if not done
    for reminder in reminders:
        schedule.every().hour.do(remind_and_open_website, reminder)

    # Reset the task flags at the end of each day
    schedule.every().day.at("23:59").do(reset_task_flags)

    while running:
        current_time = datetime.now().strftime("%H:%M")
        current_day = datetime.now().strftime("%A").lower()
        for reminder in reminders:
            if current_day in reminder["days"] and current_time >= reminder["time"] and not reminder["completed"]:
                remind_and_open_website(reminder)
        schedule.run_pending()
        time.sleep(1)  # Check every second

def start_schedule_thread():
    schedule_thread = threading.Thread(target=setup_schedule)
    schedule_thread.start()

def create_gui():
    global root
    root = tk.Tk()
    root.title("Reminder App")

    for reminder in reminders:
        frame = tk.Frame(root)
        frame.pack(fill="x", padx=5, pady=5)

        label = tk.Label(frame, text=reminder["name"])
        label.pack(side="left", padx=5)

        open_button = tk.Button(frame, text="Open", command=lambda r=reminder: open_website(r))
        open_button.pack(side="left", padx=5)

        done_button = tk.Button(frame, text="Mark as Done")
        done_button.config(command=lambda r=reminder, b=done_button: mark_task_done(r, b))
        done_button.pack(side="left", padx=5)

    quit_button = tk.Button(root, text="Quit", command=on_closing)
    quit_button.pack(pady=10)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

def on_closing(icon=None, item=None):
    global running, root
    running = False
    if root:
        try:
            root.destroy()
        except tk.TclError:
            pass
        root = None
    if icon:
        icon.stop()

def show_gui(icon, item):
    create_gui()

icon = Icon("Reminder App", create_image(), "Reminder App", Menu(
    MenuItem("Open", show_gui),
    MenuItem("Quit", on_closing)
))

# Run the icon in a separate thread to allow the main thread to handle the schedule loop
icon_thread = threading.Thread(target=icon.run)
icon_thread.start()

start_schedule_thread()