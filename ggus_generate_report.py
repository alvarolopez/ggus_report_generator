#!/usr/bin/env python

# Get the latest version from the following URL:
#     https://github.com/alvarolopez/ggus_report_generator
# AUTHOR: Alvaro Lopez <aloga@ifca.unican.es>

# Change it if you want to use it for your NGI without specifing
# it in the command-line
support_unit = "NGI_IBERGRID"

import getopt
import urllib
import urllib2
import time
import re
import sys
from xml.dom import minidom
import xml.parsers.expat

__version__ = 20121025


def usage():
    global support_unit
    print """usage: %s <username> <password> [-r] [-h] [-s NAME]
    Options:
        -r          Reverse sort (oldest first)
        -s NAME     Support Unit (defauts to %s)

        -h          Show this help
    """ % (sys.argv[0], support_unit)


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

login_data = {'login': login, 'pass': password}

url_login = 'https://ggus.eu/admin/login.php'
url_ticket_search = ('https://ggus.eu/ws/ticket_search.php')
xml_query = ('?writeFormat=XML'
           '&&show_columns_check=Array&ticket=&supportunit=%(support_unit)s'
           '&vo=all&user=&keyword=&involvedsupporter=&assignto=&affectedsite='
           '&specattrib=0&status=open&priority=all&typeofproblem=all&mouarea='
           '&radiotf=1&timeframe=any&from_date=&to_date=&untouched_date='
           '&orderticketsby=GHD_INT_REQUEST_ID&orderhow=descending'
           '&show_columns=REQUEST_ID;TICKET_TYPE;AFFECTED_VO;AFFECTED_SITE;'
           'PRIORITY;RESPONSIBLE_UNIT;STATUS;DATE_OF_CREATION;LAST_UPDATE;'
           'TYPE_OF_PROBLEM;SUBJECT' % {"support_unit": support_unit})

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

ticket_body = "=" * 80 + """
SITE: * %(affected_site)s *
      GGUS ID     : %(request_id)s
      Open since  : %(date_of_creation)s UTC
      Status      : %(status)s
      Description : %(subject)s
      Link        : https://gus.fzk.de/ws/ticket_info.php?ticket=%(request_id)s
""" + "=" * 80


opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(),
                              urllib2.HTTPSHandler())
urllib2.install_opener(opener)

# Make login
login_data = urllib.urlencode(login_data)
f = opener.open(url_login, login_data)
login_result = f.read()
f.close()

# Quick'n dirty
if "register_fail.php?nextpg" in login_result:
    print >> sys.stderr, "ERROR: Login unsuccessful."
    sys.exit(2)

# Get the XML report. We need to fetch first the ticket search page and then
# get # the XML report because of some silly redirection and authentication
f = opener.open(url_ticket_search)
url_xml = url_ticket_search + xml_query
f = opener.open(url_xml)
report = f.read()
f.close()

try:
    xml = minidom.parseString(report)
except xml.parsers.expat.ExpatError:
    # TODO(aloga): This is ugly. We need to change this to a more appropiate
    # parsing
    # This is an ugly hack. GGUS reports are inserting HTML entities
    # in XML documents.
    regexp = r'description=".*?"'
    report = re.sub(regexp, "", report, flags=re.M | re.S)
    xml = minidom.parseString(report)

tickets = xml.getElementsByTagName('ticket')

nr_of_tickets = len(tickets)

print message_header % locals()

if reverse:
    tickets.reverse()

res = []
for ticket in tickets:
    affected_site = ticket.getAttribute("affected_site") or "N/A"
    date_of_creation = time.strftime("%B %d %Y %H:%M",
            time.gmtime(float(ticket.getAttribute("date_of_creation"))))
    status = ticket.getAttribute("status")
    subject = ticket.getElementsByTagName("subject")[0].firstChild.data
    request_id = ticket.getAttribute("request_id")

    print ticket_body % locals()
