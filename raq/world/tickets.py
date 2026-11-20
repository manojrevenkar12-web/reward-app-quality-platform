"""Player support tickets, as players write them: in their language, vague or specific, sometimes about something
else entirely. The truth (which flow, which symptom) is kept beside the text for scoring the reader, and never
shown to it.
"""
from __future__ import annotations

from dataclasses import dataclass

from raq.keyed import rng

SYMPTOMS = ("crash", "cashout_stuck", "coins_wrong", "display_broken", "slow", "error")

FLOW_WORDS = {
    "en": {"login": ["log in", "sign in", "login", "my account"], "onboarding": ["the tutorial", "setup", "first start"],
           "play_round": ["the game", "playing", "a level", "my round"], "offerwall": ["the offers", "an offer", "the offer wall"],
           "cashout": ["cash out", "my payout", "paypal", "withdraw", "my gift card"],
           "live_event": ["the event", "the tournament", "the weekend challenge"],
           "notifications": ["notifications", "the push messages", "reminders"],
           "identity_check": ["the face scan", "verification", "the selfie check"], "settings": ["settings", "my profile"]},
    "de": {"login": ["anmelden", "einloggen", "mein konto"], "onboarding": ["das tutorial", "die einrichtung"],
           "play_round": ["das spiel", "spielen", "ein level"], "offerwall": ["die angebote", "ein angebot"],
           "cashout": ["auszahlung", "auszahlen", "paypal", "gutschein"], "live_event": ["das event", "das turnier"],
           "notifications": ["benachrichtigungen", "mitteilungen"], "identity_check": ["gesichtsscan", "verifizierung"],
           "settings": ["einstellungen", "profil"]},
    "fr": {"login": ["connexion", "me connecter", "mon compte"], "onboarding": ["le tutoriel", "la configuration"],
           "play_round": ["le jeu", "jouer", "un niveau"], "offerwall": ["les offres", "une offre"],
           "cashout": ["retrait", "paiement", "paypal", "carte cadeau"], "live_event": ["l'événement", "le tournoi"],
           "notifications": ["notifications", "les alertes"], "identity_check": ["scan du visage", "vérification"],
           "settings": ["paramètres", "profil"]},
}

SYMPTOM_PHRASES = {
    "en": {"crash": ["the app closes when I open {f}", "crashes every time on {f}", "{f} just shuts the app down", "app keeps crashing in {f}"],
           "cashout_stuck": ["{f} has been pending for days", "{f} failed and my coins are gone", "can't {f}, it just spins", "{f} never arrived"],
           "coins_wrong": ["I got coins twice after {f}", "coins jumped after {f}, is that right?", "balance looks wrong after {f}", "my coins doubled in {f}"],
           "display_broken": ["{f} looks broken, buttons overlap", "text is cut off in {f}", "{f} shows a blank screen", "can't see the button in {f}"],
           "slow": ["{f} is so slow", "{f} takes forever to load", "lagging a lot in {f}"],
           "error": ["{f} says something went wrong", "error message on {f}", "{f} shows error 500"]},
    "de": {"crash": ["die app stürzt bei {f} ab", "{f} schließt die app sofort"],
           "cashout_stuck": ["{f} hängt seit tagen", "{f} fehlgeschlagen, münzen weg", "{f} kommt nicht an"],
           "coins_wrong": ["doppelte münzen nach {f}", "kontostand falsch nach {f}"],
           "display_broken": ["{f} sieht kaputt aus", "text abgeschnitten bei {f}", "{f} zeigt nur weiß"],
           "slow": ["{f} ist sehr langsam", "{f} lädt ewig"],
           "error": ["{f} zeigt einen fehler", "fehlermeldung bei {f}"]},
    "fr": {"crash": ["l'appli plante sur {f}", "{f} ferme l'application"],
           "cashout_stuck": ["{f} en attente depuis des jours", "{f} échoué, mes pièces ont disparu"],
           "coins_wrong": ["pièces en double après {f}", "solde faux après {f}"],
           "display_broken": ["{f} est cassé, boutons superposés", "texte coupé dans {f}"],
           "slow": ["{f} est très lent", "{f} met une éternité à charger"],
           "error": ["{f} affiche une erreur", "message d'erreur sur {f}"]},
}

VAGUE = {"en": ["app not working pls fix", "why is this not working??", "help", "I want my money", "this app is a scam"],
         "de": ["app geht nicht", "hilfe bitte"], "fr": ["ça ne marche pas", "aidez-moi"]}

LANG = {"US": "en", "UK": "en", "CA": "en", "AU": "en", "DE": "de", "FR": "fr"}


@dataclass
class Ticket:
    text: str
    device: str
    app_version: str | None            # present when the in-app form sent it
    region: str
    flow: str | None                   # truth
    symptom: str | None                # truth


def _typos(text: str, r, rate: float) -> str:
    """Phone keyboards: some longer words lose or swap a letter."""
    words = text.split(" ")
    for i, wd in enumerate(words):
        if len(wd) > 4 and r.random() < rate:
            k = int(r.integers(1, len(wd) - 1))
            words[i] = wd[:k] + wd[k + 1:] if r.random() < 0.5 else wd[:k - 1] + wd[k] + wd[k - 1] + wd[k + 1:]
    return " ".join(words)


def write(seed: int, key: tuple, flow: str | None, symptom: str | None, device: str, region: str,
          version: str, vague_share: float = 0.12, form_share: float = 0.7, typo_rate: float = 0.12) -> Ticket:
    """One ticket. key names the draw, so the same ticket is written for every design."""
    r = rng(seed, "ticket", *key)
    lang = LANG.get(region, "en")
    if flow is None or symptom is None or r.random() < vague_share:
        text = str(r.choice(VAGUE[lang]))
    else:
        f = str(r.choice(FLOW_WORDS[lang][flow]))
        text = str(r.choice(SYMPTOM_PHRASES[lang][symptom])).format(f=f)
        text = _typos(text, r, typo_rate)
        if r.random() < 0.3:
            text = text.upper() if r.random() < 0.3 else text.capitalize() + "!!"
    form = r.random() < form_share
    return Ticket(text, device, version if form else None, region, flow, symptom)
