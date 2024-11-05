import sys
import json
import subprocess
import schedule
import time
import threading
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer, QTime, Qt
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

def mark_task_done(reminder, button=None):
    reminder["completed"] = True
    print(f"Task marked as done for {reminder['name']}")
    if button:
        button.setText("Already Done")
        button.setEnabled(False)

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
        time.sleep(60)  # Check once a minute

def start_schedule_thread():
    schedule_thread = threading.Thread(target=setup_schedule)
    schedule_thread.start()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reminder App")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.reminders = reminders
        self.labels = []
        self.done_buttons = []

        for reminder in self.reminders:
            label = QLabel(reminder["name"])
            layout.addWidget(label)
            self.labels.append(label)

            open_button = QPushButton("Open")
            open_button.clicked.connect(lambda _, r=reminder: open_website(r))
            layout.addWidget(open_button)

            done_button = QPushButton("Mark as Done")
            done_button.clicked.connect(lambda _, r=reminder, b=done_button: mark_task_done(r, b))
            layout.addWidget(done_button)
            self.done_buttons.append(done_button)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close)
        layout.addWidget(quit_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(60000)  # Check every minute

    def check_reminders(self):
        current_time = QTime.currentTime().toString("HH:mm")
        current_day = QTime.currentTime().toString("dddd").lower()
        for reminder in self.reminders:
            if current_day in reminder["days"] and current_time >= reminder["time"] and not reminder["completed"]:
                self.show_notification(reminder)

    def show_notification(self, reminder):
        toaster.show_toast(
            reminder["name"],
            f"Reminder: {reminder['name']}",
            duration=10,
            threaded=True
        )

def create_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

def on_closing(icon=None, item=None):
    global running
    running = False
    if icon:
        icon.stop()

def show_gui(icon, item):
    threading.Thread(target=create_gui).start()

icon = Icon("Reminder App", create_image(), "Reminder App", Menu(
    MenuItem("Open", show_gui),
    MenuItem("Quit", on_closing)
))

# Run the icon in a separate thread to allow the main thread to handle the schedule loop
icon_thread = threading.Thread(target=icon.run)
icon_thread.start()

start_schedule_thread()