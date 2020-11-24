from requests_html import HTMLSession
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email
import logging
import time
import os

SECONDS = 60
WAIT_TIME = 5 * SECONDS

def establish_logger():
	logging.basicConfig(filename='web_scrape.log',level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S%>')

def get_email_client():
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.ehlo()
	server.starttls()
	server.login(os.environ['EMAIL_ADDRESS'], os.environ['GMAIL_APP_PASS'])
	return server

def send_text(product_title, product_status, link, sent_already):
	if sent_already:
		return

	server = get_email_client()

	text = "{} page shows the rack is: {}\n {}".format(product_title, product_status, link)

	from_addr = os.environ['EMAIL_ADDRESS']
	to_addr = os.environ['PHONE_NUMBER_EMAIL']
	
	msg = MIMEMultipart()
	msg['From'] = from_addr
	msg['To'] = to_addr
	msg['Subject'] = "Gym Equipment Status Update"

	msg.attach(MIMEText(text.encode('utf-8'), _subtype='html', _charset="UTF-8"))

	logging.info("Sending text to Kurush about status update...")
	try:
		server.sendmail(from_addr, to_addr, msg.as_string())
		server.quit()
	except Exception as e:
		logging.error("Failed to send text!")
		logging.error(e)

def main():
	found_rack = False
	found_dips = False

	# Use tiny url because tmobile thinks other link is spam
	urls = ["https://t.ly/XJFr", "https://www.repfitness.com/rep-power-rack-dip-attachment"]
	session = HTMLSession()

	for url in urls:
		resp = session.get(url)

		product_title = resp.html.find("h1.page-title", first=True).text
		product_info = resp.html.find("div.product-info-stock-sku", first=True)
		
		product_status = None
		use_div = False

		# This check is due to the company's website having inconsistent formats for their HTML page :(
		if len(product_info.find('p.unavailable')) > 0:
			product_status = product_info.find('p.unavailable', first=True)
		elif len(product_info.find('div.unavailable')) > 0:
			product_status = product_info.find('div.unavailable', first=True)
			use_div = True
		
		# Check stock of item
		if product_status is not None and product_status.text == 'Out of Stock':
			logging.info("{} still out of stock...checking again in a 5 mins".format(product_title))
		else:
			logging.info("Found an item!")

			sent_already = False
			# This tells us if we already sent a text for this items availbility
			if found_rack and '1100' in product_title or found_dips and 'dips' in product_title:
				sent_already = True

			if use_div:
				product_status = product_info.find('div.stock', first=True)
			else:
				product_status = product_info.find('p.stock', first=True)
 
			logging.info("{} page shows the rack is: {}".format(product_title, product_status.text))
			send_text(product_title, product_status.text, url, sent_already)
			

			# Update that we've sent a text for this item
			if '1100' in product_title:
				found_rack = True
			else:
				found_dips = True
			# Lets sleep for a second so as to not rate limit our email server
			time.sleep(1)
		
	logging.info("")
	# Let's check back in 5 minutes
	time.sleep(WAIT_TIME)

establish_logger()
while True:
    main()
