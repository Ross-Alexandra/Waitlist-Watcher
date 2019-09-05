from tkinter import Tk, Label, Button, Entry, OptionMenu, StringVar, IntVar, Toplevel, Checkbutton, messagebox
from check_class import get_seat_info
import smtplib
from email.mime.text import MIMEText
from random import random
from bs4 import BeautifulSoup
import requests

class CourseChecker:
    def __init__(self, master):

        master.geometry("300x400")
        master.resizable(width=False, height=False)

        self.master = master
        master.title("Notifying Waitlist")

        self.notify_on_waitlist_checkbutton = None

        #: Inputs.
        self.subject_code_label = Label(master, text="Subject Code (eg: SENG)")
        self.subject_code_label.place(x=150, y=25, anchor="center")

        self.subject_code_entry = Entry(master)
        self.subject_code_entry.place(x=150, y=45, anchor="center")

        self.course_number_label = Label(master, text="Course Number (eg: 275)")
        self.course_number_label.place(x=150, y=75, anchor="center")

        self.course_number_entry = Entry(master)
        self.course_number_entry.place(x=150, y=95, anchor="center")

        self.section_label = Label(master, text="Section (eg: A01)")
        self.section_label.place(x=150, y=125, anchor="center")

        self.section_entry = Entry(master)
        self.section_entry.place(x=150, y=145, anchor="center")

        self.email_label = Label(master, text="Enter your email")
        self.email_label.place(x=150, y=175, anchor="center")

        self.email_entry = Entry(master)
        self.email_entry.place(x=150, y=195, anchor="center")

        self.term_selection_label = Label(master, text="Select a term")
        self.term_selection_label.place(x=10, y=225, anchor='w')

        self.term_selector = StringVar(master)
        self.term_selector.set("Fall")
        term_selection_option_menu = OptionMenu(master, self.term_selector, "Fall", "Winter", "Summer")
        term_selection_option_menu.place(x=10, y=250, anchor="w", height=25)

        self.interval_entry = Entry(master)
        self.interval_entry.place(x=290, y=250, anchor='e')

        self.interval_label = Label(master, text="Ping interval (s) (min 120s)")
        self.interval_label.place(x=290, y=225, anchor='e')

        #: Outputs.
        self.seats_label = Label(master, text="Seats:")
        self.seats_label.place(x=40, y=320, anchor="center")

        self.seat_capacity_label = Label(master, text="Capacity: 0")
        self.seat_capacity_label.place(x=120, y=340, anchor="e")

        self.seat_actual_label = Label(master, text="Actual: 0")
        self.seat_actual_label.place(x=120, y=360, anchor="e")

        self.seat_remaining_label = Label(master, text="Remaining: 0")
        self.seat_remaining_label.place(x=120, y=380, anchor="e")

        self.waitlist_label = Label(master, text="Waitlist:")
        self.waitlist_label.place(x=200, y=320, anchor="center")

        self.waitlist_capacity_label = Label(master, text="Capacity: 0")
        self.waitlist_capacity_label.place(x=280, y=340, anchor="e")

        self.waitlist_actual_label = Label(master, text="Actual: 0")
        self.waitlist_actual_label.place(x=280, y=360, anchor="e")

        self.waitlist_remaining_label = Label(master, text="Remaining: 0")
        self.waitlist_remaining_label.place(x=280, y=380, anchor="e")

        self.submit_button = Button(master, text="Submit", command=self.submit_info)
        self.submit_button.place(x=75, y=290, anchor="center", width=125, height=35)

        self.watch_button = Button(master, text="Watch Course", command=self.watch_for_course)
        self.watch_button.place(x=225, y=290, anchor="center", width=125, height=35)

    def get_course_info(self):
        subject_code = self.subject_code_entry.get().strip().upper()
        course_number = self.course_number_entry.get().strip()
        section = self.section_entry.get().strip().upper()
        term = self.term_selector.get().strip()

        course_number = int(course_number) if len(course_number) != 0 else 0

        return subject_code, course_number, section, term

    def submit_info(self):
        subject_code, course_number, section, term = self.get_course_info()

        seats = get_seat_info(subject_code, course_number, section, term)
        self.seat_capacity_label.config(text="Capacity: {}".format(seats["Seats"]["Capacity"]))
        self.seat_actual_label.config(text="Actual: {}".format(seats["Seats"]["Actual"]))
        self.seat_remaining_label.config(text="Remaining: {}".format(seats["Seats"]["Remaining"]))

        self.waitlist_capacity_label.config(text="Capacity: {}".format(seats["Waitlist"]["Capacity"]))
        self.waitlist_actual_label.config(text="Actual: {}".format(seats["Waitlist"]["Actual"]))
        self.waitlist_remaining_label.config(text="Remaining: {}".format(seats["Waitlist"]["Remaining"]))

    def watch_for_course(self):
        subject_code, course_number, section, term = self.get_course_info()
        seats = get_seat_info(subject_code, course_number, section, term)

        #: Create the window and define window parameters.
        watch_window = Toplevel(self.master)
        watch_window.grab_set()
        watch_window.geometry("320x115")
        watch_window.resizable(False, False)
        watch_window.title("Watcher")
        watch_window.protocol("WM_DELETE_WINDOW", lambda: self.close_child_window(watch_window))

        self.master.withdraw()

        #: Define the labels that will be used.
        course_label = Label(watch_window, text="{} {} {} watcher".format(subject_code, course_number, section))
        remaining_seat_label = Label(watch_window, text="Seats remaining: {}".format(seats["Seats"]["Remaining"]))
        remaining_waitlist_label = Label(watch_window, text="Waitlist seats remaining: {}" \
                                         .format(seats["Waitlist"]["Remaining"]))

        mins, secs = divmod(self.get_interval() / 1000, 60)
        timestamp = str(mins) + " mins " + str(secs) + " secs"

        time_remaining_label = Label(watch_window, text="Ping interval (min 120s): {}".format(timestamp))

        #: Define the buttons that will be used.
        close_button = Button(watch_window, text="Close", command=lambda: self.close_child_window(watch_window))

        #: Define the checkbox for notifying on open waitlist seats.
        self.notify_on_waitlist_checkbutton = IntVar()
        notify_waitlist = Checkbutton(watch_window, text="Notify me on waitlist openings too.",
                                      variable=self.notify_on_waitlist_checkbutton)

        #: Place the defined objects on the window.
        course_label.place(x=160, y=10, anchor="center")
        remaining_seat_label.place(x=300, y=50, anchor="e")
        remaining_waitlist_label.place(x=300, y=65, anchor="e")
        time_remaining_label.place(x=160, y=30, anchor="center")
        close_button.place(x=160, y=105, anchor="center", width=125, height=20)
        notify_waitlist.place(x=160, y=85, anchor="center")

        self.master.after(1000, lambda: self.update_watch_window(
            remaining_seat_label,
            remaining_waitlist_label,
            time_remaining_label,
            self.get_interval()
        )
                          )

    def update_watch_window(self, seat_label, waitlist_label, time_label, cur_interval):
        cur_interval -= 1000

        if cur_interval < 0:
            subject_code, course_number, section, term = self.get_course_info()
            seats = get_seat_info(subject_code, course_number, section, term)

            notify_on_waitlist = self.notify_on_waitlist_checkbutton.get()

            if seats["Seats"]["Remaining"] > 0:
                self.notify_openings(self.email_entry.get(), seats["Seats"]["Remaining"],
                                     subject_code, course_number, section)
            elif seats["Waitlist"]["Remaining"] > 0 and notify_on_waitlist:
                self.notify_openings(self.email_entry.get(), seats["Waitlist"]["Remaining"],
                                     subject_code, course_number, section, wl=True)

            seat_label.config(text="Seats remaining: {}".format(seats["Seats"]["Remaining"]))
            waitlist_label.config(text="Waitlist seats remaining: {}".format(seats["Waitlist"]["Remaining"]))
            cur_interval = self.get_interval() + 1000

        else:
            mins, secs = divmod(cur_interval / 1000, 60)
            timestamp = str(mins) + " mins " + str(secs) + " secs"
            time_label.config(text="Seconds until next ping: {}".format(timestamp))

        self.master.after(1000 + int((random() * 240) - 120),
                          lambda: self.update_watch_window(seat_label, waitlist_label, time_label, cur_interval))

    def close_child_window(self, window):
        window.destroy()
        self.master.deiconify()

    def get_interval(self):
        raw = self.interval_entry.get()
        raw = int(raw) if len(raw) > 0 and int(raw) >= 120 else 120

        return raw * 1000

    def warn(self, title: str, msg: str):
        messagebox.showwarning(title, msg)

    def notify_openings(self, addr, open_seats, subject_code, course_number, section, wl=False):
        web_addr = addr[addr.index('@') + 1:addr.index('.')].lower()

        server_address = ""

        if web_addr == "hotmail":
            server_address = "hotmail-com.olc.protection.outlook.com"
        elif web_addr == "outlook":
            server_address = "outlook-com.olc.protection.outlook.com"
        elif web_addr == "live":
            server_address = "live-com.olc.protection.outlook.com"
        elif web_addr == "mail":
            server_address = "mx00.mail.com"
        elif web_addr == "yahoo":
            server_address = "mta5.am0.yahoodns.net"
        elif web_addr == "icloud":
            server_address = "mx1.mail.icloud.com"
        elif web_addr == "uvic":
            server_address = "smtpy.uvic.ca"
        else:
            server_address = "gmail-smtp-in.l.google.com"

        try:
            server = smtplib.SMTP(server_address, timeout=3)
        except Exception as e:
            print(e)
            response = requests.get("http://www.showmyisp.com/")
            soup = BeautifulSoup(response.content, "lxml")

            isp_row = soup.findAll("td", string="ISP")[0].parent
            isp = isp_row.find_all("td", "td2")[0].string

            if "telus" in isp.lower():
                server_address = "mail.telus.net"
            elif "shaw" in isp.lower():
                server_address = "mail.shaw.ca"
            elif "lightspeed" in isp.lower():
                server_address = "mail.lightspeed.ca"
            elif "at&t" in isp.lower():
                server_address = "smtp1.attglobal.net"
            elif "dccnet" in isp.lower():
                server_address = "mail.dccnet.com"
            else:
                self.warn("WARNING", "Your ISP is blocking communications over port 25 and has no listed STMP server."
                                     "\nas such it is impossible to send an email to you from this address. Sorry for"
                                     "\nthe Inconvenience.")
                exit()
            server = smtplib.SMTP(server_address, timeout=3)

        msg = "Hi,\n\n" \
              "" \
              "This email is to inform you that {} {}seat{} have opened up for {} {} {}.\n\n" \
              "" \
              "Thank you for using the waitlist simulator, \n\n" \
              "" \
              "Have a great day." \
            .format(open_seats, "waitlist-" if wl else "", "s" if open_seats > 1 else "",
                    subject_code, course_number, section)

        msg = MIMEText(msg)
        msg["Subject"] = "{}Opening in {} {} {}".format(
            "waitlist " if wl else "",
            subject_code,
            course_number,
            section
        )
        msg["From"] = "Waitlist Watcher <WaitlistWatcher@InternalSystem.ca>"
        msg["To"] = addr

        server.send_message(msg)
        server.quit()


if __name__ == "__main__":
    root = Tk()
    gui = CourseChecker(root)
    root.mainloop()
