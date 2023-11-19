import requests, json
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def make_text_content(plates):
    final_results = ''
    for plate in plates:
        arabicVariantFound, series, registrationNumber, latestUpdateDate = plate
        if series != "" :
            # TN
            final_results += series + arabicVariantFound + registrationNumber + 'Dernier mise a jour : ' + str(latestUpdateDate) + '\n'
        else:
            final_results += arabicVariantFound + registrationNumber + 'Dernier mise a jour : ' + str(latestUpdateDate) + '\n'

    return final_results

def make_html_plates(plates):
    html_plates = []
    for plate in plates:
        arabicVariantFound, series, registrationNumber, latestUpdateDate = plate
        if series != "" :
            # TN
            this_plate_dom = f"""
            <span style="margin-left:auto;margin-right:auto;display: block;width: 250px;border-radius: 7px;background-color: black;">
                <span style="display: table;width: 100%;color:white;font-size:30px;padding-top:0.75rem;padding-bottom:0.75rem;border-color:white;border-width: 2px;margin-left:0.25rem;margin-right:0.25rem;">
                <div class="empty-element" style="width: 10px;"></div>
                <span style="display: table-cell;width: 33.33%;">{series}</span>
                <div style="width: 10px;"></div>
                <span style="display:block;">{arabicVariantFound}</span>
                <span style="display: table-cell;width: 33.33%;">{registrationNumber}</span>
                </span>
                <span style="display: block;text-align:center;font-size:10px;color: white;">{str(latestUpdateDate)}</span>
            </span>
            """
        else:
            this_plate_dom = f"""
            <span style="margin-left:auto;margin-right:auto;display: block;width: 250px;border-radius: 7px;background-color: black;">
                <span style="display: table;width: 100%;color:white;font-size:30px;padding-top:0.75rem;padding-bottom:0.75rem;border-color:white;border-width: 2px;margin-left:0.25rem;margin-right:0.25rem;">
                <div class="empty-element" style="width: 40px;"></div>
                <span style="display: table-cell;width: 25%;">{arabicVariantFound}</span>
                <span style="display: table-cell;width: 55%;">{registrationNumber}</span>
                <div class="empty-element" style="width: 10px;"></div>
                </span>
                <span style="display: block;text-align:center;font-size:10px;color: white;">{str(latestUpdateDate)}</span>
            </span>
            """
        html_plates.append(this_plate_dom)
    return html_plates


def make_html_content(plates):
    html_plates = make_html_plates(plates)
    html_text = ''

    for plate in html_plates:
        html_text += plate + '<br>'

    with open('defaultTemplate.html', 'r') as file:
        template = file.read()
    template = template.replace('<span id="plates"></span>', html_text)
    print(template)
    return template

def lambda_handler(event, context):
    r = requests.get('https://www.automobile.tn/fr/guide/dernieres-immatriculations.html', verify=False)

    soup = BeautifulSoup(r.text, "html.parser")

    mainDiv = soup.find('div', {'class', 'cms-prose'})
    print('Main Div Found')

    # Second P Tag in that Div
    spanOfPlates = mainDiv.find_all('p')[1].find_all('span', {'class','mx-auto'})
    print(f'{len(spanOfPlates)} Plates Found')

    #
    plates = []
    for imm in spanOfPlates:
        plate_numberContainer, latestUpdateDateContainer = imm.find_all('span', recursive=False)
        
        latestUpdateDate = datetime.strptime(latestUpdateDateContainer.text, "%d.%m.%Y %H:%M")
        
        arabicVariantFound = plate_numberContainer.find('span', {'class':'-mt-1 block'}).text

        if arabicVariantFound=='تونس' :
            # We will save it in this format registration number = series:registrationNumber
            series              = plate_numberContainer.find('span', {'class':''}).text
            registrationNumber  = plate_numberContainer.find('span', {'class':'tabular-nums'}).text
        else:
            series              = ""
            registrationNumber  = plate_numberContainer.find('span', {'class':'tabular-nums'}).text
    
        plates.append([arabicVariantFound, series, registrationNumber, latestUpdateDate])

    smtp_server = "smtp.gmail.com"
    smtp_port = 465  # For SSL
    password = "itigggjajmcerwek"

    sender_email = receiver_email = "chedychaaben@gmail.com"
    message = MIMEMultipart("alternative")
    message['Subject'] = 'Python Script Results'
    message['From'] = 'chedychaaben@gmail.com'
    message['To'] = 'chedychaaben@gmail.com'

    text_content = make_text_content(plates)
    html_content = make_html_content(plates)

    # Create plain text part
    text_part = MIMEText(text_content, 'plain')
    message.attach(text_part)

    # Create HTML part
    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)


    # Create secure connection with server and send email
    context = ssl.create_default_context()
    # Create an SMTP connection using SMTP_SSL and a context manager
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        # Login to the SMTP server
        server.login(sender_email, password)
        # Send the email
        server.sendmail(sender_email, receiver_email, message.as_string())
    return {
        'statusCode': 200,
        'body': json.dumps('OK!')
    }
