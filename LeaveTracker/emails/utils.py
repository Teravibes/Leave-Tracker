from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import now


def send_custom_email(subject, to_email, context, html_template, text_template=None):
    context["current_year"] = now().year
    html_content = render_to_string(html_template, context)
    text_content = render_to_string(text_template, context) if text_template else None

    msg = EmailMultiAlternatives(subject, text_content or '', to=[to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
