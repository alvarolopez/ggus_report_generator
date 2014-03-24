#!/usr/bin/env python

# Get the latest version from the following URL:
#     https://github.com/alvarolopez/ggus_report_generator
# AUTHOR: Alvaro Lopez <aloga@ifca.unican.es>

import argparse
import requests
import xml.parsers.expat

from xml.dom import minidom

__version__ = 20140324

# Change it if you want to use it for your NGI without specifing
# it in the command-line
SUPPORT_UNIT = "NGI_IBERGRID"

message_header = """
### Open GGUS tickets ###

There are %(ticket count)s open tickets under %(support_unit)s scope. Please
find below a short summary of them. Please take the appropriate actions:
    - Change the ticket status from "ASSIGNED" to "IN PROGRESS".
    - Provide feedback on the issue as regularly as possible.
    - In case of problems, ask for help in <ibergrid-ops@listas.cesga.es>
    - For long pending issues, put your site/node in downtime.
    - Don't forget to close the ticket when you have solved the problem.
"""


class GGUSReportException(Exception):
    pass


class GGUSTicket(object):
    body_template = "=" * 80 + """
SITE: * %(affected_site)s *
      GGUS ID     : %(request_id)s
      Open since  : %(date_of_creation)s UTC
      Status      : %(status)s
      Description : %(subject)s
      Link        : https://gus.fzk.de/ws/ticket_info.php?ticket=%(request_id)s
""" + "=" * 80

    def __init__(self, ticket):
        self.ticket = ticket

    def _get_by_xml_tag(self, tag):
        value = self.ticket.getElementsByTagName(tag)[0].firstChild.nodeValue
        return value or "N/A"

    @property
    def affected_site(self):
        return self._get_by_xml_tag("affected_site")

    @property
    def date_of_creation(self):
        return self._get_by_xml_tag("date_of_creation")

    @property
    def status(self):
        return self._get_by_xml_tag("status")

    @property
    def subject(self):
        return self._get_by_xml_tag("subject")

    @property
    def request_id(self):
        return self._get_by_xml_tag("request_id")

    def render(self):
        return self.body_template % {"request_id": self.request_id,
                                     "affected_site": self.affected_site,
                                     "date_of_creation": self.date_of_creation,
                                     "status": self.status,
                                     "subject": self.subject}


class GGUSConnection(object):
    url = ("https://ggus.eu/index.php?mode=ticket_search&ticket_id="
           "&supportunit=%(support_unit)s&su_hierarchy=0&vo=all&user="
           "&keyword=&involvedsupporter=&assignedto=&affectedsite="
           "&specattrib=none&status=open&priority=&typeofproblem=all"
           "&ticket_category=all&mouarea=&date_type=creation+date"
           "&tf_radio=1&timeframe=any&from_date=&to_date=&untouched_date="
           "&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO%%21"
           "&writeFormat=XML")

    def __init__(self, user, password, support_unit):
        self.session = None
        self.user = user
        self.password = password
        self.url = self.url % {"support_unit": support_unit}

    def _get_ggus_session(self):
        s = requests.Session()
        s.verify = False
        data = {"login": self.user, "password": self.password}
        url = "https://ggus.eu/index.php?mode=login"
        s.post(url, data=data)

        self.session = s

    def login(self):
        self._get_ggus_session()
        if not self.session.cookies:
            raise GGUSReportException("Could not authenticate with GGUS")

    def tickets(self):
        if not self.session:
            self.login()

        r = self.session.get(self.url)

        try:
            aux = minidom.parseString(r.content)
        except xml.parsers.expat.ExpatError:
            raise GGUSReportException("Could not parse XML content")

        tickets = aux.getElementsByTagName('ticket')

        return [GGUSTicket(ticket) for ticket in tickets]


def parse_args():
    global SUPPORT_UNIT
    parser = argparse.ArgumentParser(description='TBD.')
    parser.add_argument('username',
                        metavar='USERNAME',
                        type=str,
                        help='GGUS username.')

    parser.add_argument('password',
                        metavar='PASSWORD',
                        type=str,
                        help='GGUS user password.')

    parser.add_argument('-s', '--support-unit',
                        dest='support_unit',
                        metavar='SUPPORT_UNIT',
                        default=SUPPORT_UNIT,
                        help=('Only tickets belonging to this support unit '
                              'will be collected'))

    parser.add_argument('-r', '--reverse',
                        dest='reverse',
                        default=False,
                        action='store_true',
                        help='Sort tickets in reverse chronological order.')

    return parser.parse_args()


def main():
    args = parse_args()

    ggus = GGUSConnection(args.username,
                          args.password,
                          args.support_unit)

    tickets = ggus.tickets()

    if args.reverse:
        tickets.reverse()

    print message_header % {"support_unit": args.support_unit,
                            "ticket count": len(tickets)}
    for ticket in tickets:
        print ticket.render()


if __name__ == "__main__":
    main()
