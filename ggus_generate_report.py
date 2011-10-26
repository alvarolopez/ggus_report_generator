#!/usr/bin/env python

# Get the latest version from http://devel.ifca.es/~alvaro/files/ggus_generate_report.py
# AUTHOR: Alvaro Lopez <aloga@ifca.unican.es>

__version__ = 20110530

import urllib
import urllib2

import time

from xml.dom import minidom

import sys

if len(sys.argv) != 3:
    print "ERROR. Usage %s <username> <password>" % sys.argv[0]
    sys.exit(1)

login = sys.argv[1]
password = sys.argv[2]

login_data = {'login': login, 'pass': password}

url_login = 'https://ggus.eu/admin/login.php'
url_xml = 'https://gus.fzk.de/ws/ticket_search.php?writeFormat=XML&&show_columns_check=Array&ticket=&supportunit=NGI_IBERGRID&vo=all&user=&keyword=&involvedsupporter=&assignto=&affectedsite=&specattrib=0&status=open&priority=all&typeofproblem=all&mouarea=&radiotf=1&timeframe=lastyear&tf_date_day_s=&tf_date_month_s=&tf_date_year_s=&tf_date_day_e=&tf_date_month_e=&tf_date_year_e=&lm_date_day=24&lm_date_month=8&lm_date_year=2010&orderticketsby=GHD_AFFECTED_SITE&orderhow=ascending&show_columns=REQUEST_ID;AFFECTED_SITE;STATUS;DATE_OF_CREATION;LAST_UPDATE;SHORT_DESCRIPTION'

message_header = """
### Open GGUS tickets ###

There are %(nr_of_tickets)s open tickets under IBERGRID scope. Please find below a
short summary of those tickets. Please take the appropriate actions:
    - Change the ticket status from "ASSIGNED" to "IN PROGRESS".
    - Provide feedback on the issue as regularly as possible.
    - In case of problems, ask for help in ibergrid-ops@listas.cesga.es
    - For long pending issues, put your site/node in downtime.
    - Don't forget to close the ticket when you have solved the problem."""

ticket_body = """
===============================================================================
SITE : * %(affected_site)s *
        GGUS ID     : %(request_id)s
        Open since  : %(date_of_creation)s UTC
        Status      : %(status)s
        Description : %(short_description)s
        Link        : https://gus.fzk.de/ws/ticket_info.php?ticket=%(request_id)s
==============================================================================="""


opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
urllib2.install_opener(opener)

# Make login
login_data = urllib.urlencode(login_data)
f = opener.open(url_login, login_data)
f.close()

# Get the XML report
f = opener.open(url_xml)
report = f.read()
f.close()

xml = minidom.parseString(report)
tickets = xml.getElementsByTagName('ticket')

nr_of_tickets = len(tickets)

print message_header % locals()

for ticket in tickets:
    affected_site = ticket.getAttribute("affected_site")
    date_of_creation = time.strftime("%B %d %Y %H:%M",time.gmtime(float(ticket.getAttribute("date_of_creation"))))
    status = ticket.getAttribute("status")
    short_description = ticket.getElementsByTagName("short_description")[0].firstChild.data
    request_id = ticket.getAttribute("request_id")

    print ticket_body % locals()

