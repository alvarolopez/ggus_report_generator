#!/usr/bin/env python

# Get the latest version from the following URL:
#     https://github.com/alvarolopez/ggus_report_generator
# AUTHOR: Alvaro Lopez <aloga@ifca.unican.es>

# Change it if you want to use it for your NGI without specifing
# it in the command-line
support_unit = "NGI_IBERGRID"

import getopt
import requests
import sys
import time
import xml.parsers.expat

from xml.dom import minidom

__version__ = 20140324

class GGUSReportException(Exception):
    pass

def usage():
    global support_unit
    print """usage: %s <username> <password> [-r] [-h] [-s NAME]
    Options:
        -r          Reverse sort (oldest first)
        -s NAME     Support Unit (defauts to %s)

        -h          Show this help
    """ % (sys.argv[0], support_unit)

def get_ggus_session(login, password):
    s = requests.Session()
    s.verify = False
    data = {"login": login, "password": password}
    url = "https://ggus.eu/index.php?mode=login"
    s.post(url, data=data)

    return s

def get_ticket_value(ticket, tag):
    return ticket.getElementsByTagName(tag)[0].firstChild.nodeValue

try:
    opts, args = getopt.getopt(sys.argv[1:], 'rhs:')
except getopt.GetoptError, err:
    print >> sys.stderr, "ERROR: " + str(err)
    usage()
    sys.exit(1)

reverse = False
for o, a in opts:
    if o == "-h":
        usage()
        sys.exit(0)
    elif o == "-s":
        support_unit = a
    elif o == "-r":
        reverse = True

if len(args) != 2:
    print "ERROR. Usage %s <username> <password>" % sys.argv[0]
    sys.exit(1)

login = args.pop(0)
password = args.pop(0)

ticket_body = "=" * 80 + """
SITE: * %(affected_site)s *
      GGUS ID     : %(request_id)s
      Open since  : %(date_of_creation)s UTC
      Status      : %(status)s
      Description : %(subject)s
      Link        : https://gus.fzk.de/ws/ticket_info.php?ticket=%(request_id)s
""" + "=" * 80

message_header = """
### Open GGUS tickets ###

There are %(nr_of_tickets)s open tickets under IBERGRID scope. Please find
below a short summary of those tickets. Please take the appropriate actions:
    - Change the ticket status from "ASSIGNED" to "IN PROGRESS".
    - Provide feedback on the issue as regularly as possible.
    - In case of problems, ask for help in ibergrid-ops@listas.cesga.es
    - For long pending issues, put your site/node in downtime.
    - Don't forget to close the ticket when you have solved the problem.
"""

url = ("https://ggus.eu/index.php?mode=ticket_search&ticket_id="
       "&supportunit=%(support_unit)s&su_hierarchy=0&vo=all&user="
       "&keyword=&involvedsupporter=&assignedto=&affectedsite="
       "&specattrib=none&status=open&priority=&typeofproblem=all"
       "&ticket_category=all&mouarea=&date_type=creation+date"
       "&tf_radio=1&timeframe=any&from_date=&to_date=&untouched_date="
       "&orderticketsby=REQUEST_ID&orderhow=desc&search_submit=GO%%21"
       "&writeFormat=XML" % {"support_unit": support_unit})


s = get_ggus_session(login, password)
if not s.cookies:
    raise GGUSReportException("Could not authenticate with GGUS")
r = s.get(url)

try:
    xml = minidom.parseString(r.content)
except xml.parsers.expat.ExpatError:
    raise GGUSReportException("Could not parse XML content") 

tickets = xml.getElementsByTagName('ticket')
nr_of_tickets = len(tickets)

print message_header % locals()

if reverse:
    tickets.reverse()

res = []
for ticket in tickets:
    affected_site    = get_ticket_value(ticket, "affected_site") or "N/A"
    date_of_creation = get_ticket_value(ticket, "date_of_creation")
    status           = get_ticket_value(ticket, "status")
    subject          = get_ticket_value(ticket, "subject")
    request_id       = get_ticket_value(ticket, "request_id")

    print ticket_body % locals()

