# Configuring Anymail

## Requirements

1. AWS Account
2. Add SES permissions to user by IAM service

## Configuration

### Direct SES

1. Add AWS ID, SECRET key and region to .env
2. Set EMAIL_BACKEND var with anymail.backends.amazon_ses.EmailBackend

### SMTP
To send email using the Amazon SES SMTP interface, you must connect to an SMTP endpoint

1. Create your smtp credentials (if doesn't exists)
2. Set EMAIL variables in .env


### About sendbox mode (restrictions)
* When in the sandbox, you can only send email to the Amazon SES mailbox simulator and verified email addresses or domains.Request to be moved out of the sandbox by updating your account details.

* To test emails in sandbox mode, go to Identity Management and add the email addresses

More: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/request-production-access.html?icmpid=docs_ses_console







