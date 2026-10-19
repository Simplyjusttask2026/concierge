"""Outreach gates. Nothing sends without explicit env flags + owner approval."""
import os
OWNER_GO_CALLS = os.environ.get("SJT_GO_CALLS", "") == "1"
OWNER_GO_TEXTS = os.environ.get("SJT_GO_TEXTS", "") == "1"
OWNER_GO_EMAILS = os.environ.get("SJT_GO_EMAILS", "") == "1"

def can_email():
    return OWNER_GO_EMAILS
def can_call(number_e164, approved_numbers):
    return OWNER_GO_CALLS and number_e164 in approved_numbers
def can_text(number_e164, approved_numbers):
    return OWNER_GO_TEXTS and number_e164 in approved_numbers

RETELL_AGENT_ID = "agent_d2376fb2cafc3357aa8078f70f"  # exists, 0 phone numbers - do not auto-buy
ZOHO_MAIL_ACCOUNT_ID = "8048488000000008002"  # tasksupport@simplyjusttask.com
BOOKING = "https://cal.com/simply-just-task/simplybook"
