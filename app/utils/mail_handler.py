import smtplib
from email.mime.text import MIMEText
from app.config.config import Settings
from app.utils.jinja import template_env
from app.utils.logger import Logger
from app.models import db_models as model

email_cfg = Settings().email
LOGGER = Logger().start_logger()


class MailHandler:
    def __init__(self):
        self.server = smtplib.SMTP(host=email_cfg['host'], port=int(email_cfg['port']))
        # self.server.ehlo()
        self.email_from = email_cfg.get("admin_mail")
        self.domain = email_cfg.get("domain_name")

    def send_email(self, email_to: str, subject: str, body: str):
        mail = MIMEText(body, 'html')
        mail['From'] = "no.reply@statuspulse.app"
        mail['To'] = email_to
        mail['Subject'] = subject
        # self.server.login(email_cfg['username'], email_cfg['password'])
        mail_resp = self.server.send_message(mail)
        LOGGER.debug(f"Mail response: {mail_resp}")

    def send_new_account(self, email_to: str):
        template = template_env.get_template("new_account.html")
        email_body = template.render(website_url=self.domain)
        self.send_email(email_to, "New Registration", email_body)

    def send_pass_reset(self, email_to: str, token: str):
        template = template_env.get_template("password_reset.html")
        reset_link = f"{self.domain}/password-reset?tkn={token}"
        email_body = template.render(reset_link=reset_link, user_email=email_to, website_url=self.domain)
        self.send_email(email_to, "Забравена парола", email_body)

    def send_confirm_pass_reset(self, email_to: str):
        template = template_env.get_template("confirm_password_reset.html")
        email_body = template.render(user_email=email_to, website_url=self.domain)
        self.send_email(email_to, "Успешно променена парола", email_body)
