from bs4 import BeautifulSoup
import argparse
from datetime import datetime
import requests


def get_seat_info(course_code: str, course_number: int, section: str, s_term: str):
    """ get_seat_info(str, int, str, str)

        Get a dictionary containing the capacity, actual, and remaining
        number of both seats, and waitlist seats.

        Args:
            course_code(str): The code for the course type (eg: SENG)
            course_number(int): The number of the course (eg: 275)
            section(str): The section to check (eg: A01, B01, or T01)
            s_term(str): The term that this section is in (Summer, Winter, or Fall)
        Returns:
             {
                Seats: {
                    Capacity: [total number of seats],
                    Actual: [total number of taken seats],
                    Remaining: [total number of remaining seats]
             }
                 Waitlist: {
                     Capacity: [total number of waitlist seats],
                     Actual: [total number of taken waitlist seats],
                     Remaining: [total number of remaining waitlist seats]
                 }
             }
    """

    #: Get the month number of the selected term (for use in the url).
    term = {"Winter": "01", "Summer": "05", "Fall": "09"}[s_term]

    now = datetime.today()

    #: No need to check courses in the past, thus if a request is made
    #: for a term whose month is before ours, assume that the user
    #: actually wants to know about next year's term. For example, if
    #: a used asks about the Winter term in December 2017, assume they want
    #: January 2018's term, and not January 2017's term.
    if now.month > int(term):
        add_year = 1
    else:
        add_year = 0

    #: Create the term_in variable used in the url. It is YYYYMM format.
    term_in = str(datetime.today().year + add_year) + term

    #: The url with which to find the course with.
    course_search_url = "https://www.uvic.ca/BAN1P/bwckctlg.p_disp_listcrse" \
                        "?term_in={}&subj_in={}&crse_in={}&schd_in=" \
        .format(term_in, course_code, course_number)

    #: Get the html page for the generated url, and create a soup.
    response = requests.get(course_search_url)
    soup = BeautifulSoup(response.content, "lxml")

    #: Get all th tags with a class that is ddtitle.
    course_samples = soup.find_all("th", "ddtitle")

    #: Loop through all of the found th tags, until we find one whose
    #: string has the requested section in it. Then grab the url in the
    #: href assosiated with that, this is the url of the page that has
    #: seat information in it.
    seat_capacity_url = None
    for th in course_samples:

        #: th.a.string will look something like:
        #: 	SENG 275 - B01 - ######
        #: thus, if the requested section (eg B01) is in
        #: this string, then this is the correct th.
        if section in th.a.string:
            #: If this is the correct th, then grab the href assosiated
            #: with it, as this is the link to the page with seat info.
            seat_capacity_url = "https://www.uvic.ca" + th.a.attrs['href']

            #: break to save time.
            break

    #: If there was no found url, then the section was not in any of the th's.
    #: This means that either something has changed with the website, or more likely
    #: the class does not have a section matching the requested section.
    if seat_capacity_url is None:
        print("{} does not match any existing sections for {} {} in the {} term." \
              .format(section, course_code, course_number, s_term))
        return {"Seats": {
            "Capacity": 0,
            "Actual": 0,
            "Remaining": 0
        },
            "Waitlist": {
                "Capacity": 0,
                "Actual": 0,
                "Remaining": 0
            }
        }

    #: Get the html page for the url with seat capacities, and create a soup.
    response = requests.get(seat_capacity_url)
    soup = BeautifulSoup(response.content, "lxml")

    #: Find the span that is the label for Seats, and find its parent's parent.
    #: This is the row of the table holding the information on the class's seat
    #: information.
    seats_label = soup.findAll("span", string="Seats")[0]
    seats_row = seats_label.parent.parent

    #: Get the numbers for capacity, actual, and remaining seats from the
    #: table.
    cells = seats_row.findAll('td')  #: Get each cell in the table.
    seats = {  #: cells[x].string holds the value for that cell in the table.
        "Capacity": int(cells[0].string),
        "Actual": int(cells[1].string),
        "Remaining": int(cells[2].string)
    }

    #: Find the span that is the label for Waitlist seats, and find its parent's
    #: parent. this is the row of the table holding the information on the class's
    #: waitlist seats information.
    waitlist_label = soup.findAll("span", string="Waitlist Seats")[0]
    waitlist_row = waitlist_label.parent.parent

    #: Get the numbers for capacity, actual, and remaining for waitlist seats from
    #: the table.
    cells = waitlist_row.findAll('td')
    waitlist_seats = {  #: cells[x].string holds the value for that cell in the table.
        "Capacity": int(cells[0].string),
        "Actual": int(cells[1].string),
        "Remaining": int(cells[2].string)
    }

    #: Return the dictionary specified in this method's description.
    return {"Seats": seats, "Waitlist": waitlist_seats}


if __name__ == "__main__":

    #: Create an argument parser to get the information for the checker from the
    #: command line.
    parser = argparse.ArgumentParser(description="Command line utility to check for open seats in a UVIC course")

    parser.add_argument('course_code', help="The code for the course (Eg: SENG)", metavar='course-code')
    parser.add_argument('course_number', help="The number of the course (Eg: 100)", type=int, metavar='course-number')
    parser.add_argument('section', help="The section of the course (Eg: A01, or B01, or T01)")

    #: A mutually exclusive group is needed here as you can only be in one term at a time.
    #: moreover, it is required because you must specify a term.
    term_group = parser.add_mutually_exclusive_group(required=True)
    term_group.add_argument('-s', '--summer', action='store_true', help='Course in the summer term (May start)')
    term_group.add_argument('-f', '--fall', action='store_true', help='Course in the fall term (September start)')
    term_group.add_argument('-w', '--winter', action='store_true', help='Course in the winter term (January start)')

    #: Parse the arguments.
    args = parser.parse_args()

    if args.summer:
        term_arg = "Summer"
    elif args.fall:
        term_arg = "Fall"
    else:
        term_arg = "Winter"

    #: Get the seat information.
    open_seats = get_seat_info(args.course_code, args.course_number, args.section, term_arg)

    #: If open_seats == {}, then something has failed and reported, so exit.
    if open_seats == {}:
        exit()
    #: Otherwise print the information to the screen to be seen.
    else:
        for seat_type, seat_info in open_seats.items():
            print(seat_type)
            for availability_type, value in seat_info.items():
                print("\t{}:  {}".format(availability_type, value))
