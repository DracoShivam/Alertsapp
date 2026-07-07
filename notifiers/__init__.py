from notifiers.discord import DiscordNotifier
from notifiers.email import EmailNotifier
from notifiers.whatsapp import WhatsAppNotifier

NOTIFIERS = {
    "discord": DiscordNotifier,
    "email": EmailNotifier,
    "whatsapp": WhatsAppNotifier
}

def get_notifier(notifier_name: str, config: dict):
    """
    Returns an initialized instance of the notifier.
    """
    notifier_class = NOTIFIERS.get(notifier_name.lower())
    if not notifier_class:
        raise ValueError(f"Unknown notifier: {notifier_name}. Available: {list(NOTIFIERS.keys())}")
    return notifier_class(config)
