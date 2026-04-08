"""
Generate realistic sample datasets that mirror real-world IT ticket datasets.
In production, replace these with the actual CSV downloads from the sources listed in README.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random, os

np.random.seed(42)
random.seed(42)

os.makedirs("/home/claude/opsdesk/data/raw", exist_ok=True)
os.makedirs("/home/claude/opsdesk/data/processed", exist_ok=True)

CATEGORIES = ["Network", "Hardware", "Software", "Security", "Database", "Cloud", "Email", "VPN", "Printing", "Access Management"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
STATUSES = ["Open", "In Progress", "Resolved", "Closed", "Escalated"]
AGENTS = ["Alice Johnson", "Bob Martinez", "Carol White", "David Lee", "Emma Brown", "Frank Davis"]
DEPARTMENTS = ["IT", "HR", "Finance", "Operations", "Sales", "Engineering", "Legal"]
LANGUAGES = ["en", "de", "fr", "es", "pt", "nl"]

TICKET_SUBJECTS = {
    "Network": ["Cannot connect to internet", "VPN not working", "Slow network speed", "WiFi drops frequently", "Cannot access shared drive"],
    "Hardware": ["Laptop not turning on", "Monitor flickering", "Keyboard not working", "Printer jam", "Mouse not responding"],
    "Software": ["Application crashes on startup", "Cannot install software", "License expired", "Error code 0x80070057", "Software update failed"],
    "Security": ["Suspicious email received", "Account locked out", "Possible malware detected", "Unauthorized access attempt", "Password reset required"],
    "Database": ["Cannot connect to database", "Query running slowly", "Database backup failed", "Data corruption detected", "Access denied to table"],
    "Cloud": ["AWS instance not responding", "Azure storage quota exceeded", "GCP billing alert", "Docker container crash", "Kubernetes pod failing"],
    "Email": ["Outlook not syncing", "Cannot send large attachments", "Spam filter too aggressive", "Calendar invites not working", "Email bouncing back"],
    "VPN": ["VPN timeout issues", "Two-factor auth not working", "Split tunnel configuration", "Remote access denied", "VPN slow performance"],
    "Printing": ["Printer offline", "Print quality poor", "Cannot find printer on network", "Paper jammed", "Driver installation failed"],
    "Access Management": ["New employee onboarding", "Access to system needed", "Role change request", "Offboarding checklist", "SSO not working"]
}

RESOLUTIONS = [
    "Issue resolved by restarting the service.",
    "Escalated to L2 support for further investigation.",
    "Configuration updated and verified working.",
    "User credentials reset and access restored.",
    "Hardware replaced under warranty.",
    "Software reinstalled and patched to latest version.",
    "Network settings reconfigured.",
    "Third-party vendor engaged for resolution.",
    "Workaround provided while permanent fix is pending.",
    "Issue was user error, provided training."
]

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def generate_ticket_dataset(n=5000):
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 6, 30)
    rows = []
    for i in range(n):
        cat = random.choice(CATEGORIES)
        subject = random.choice(TICKET_SUBJECTS[cat])
        created = random_date(start_date, end_date)
        priority = random.choices(PRIORITIES, weights=[30, 40, 20, 10])[0]
        status = random.choices(STATUSES, weights=[10, 25, 45, 15, 5])[0]
        resolution_hours = {"Low": random.randint(24, 120), "Medium": random.randint(8, 48), "High": random.randint(2, 24), "Critical": random.randint(1, 8)}[priority]
        resolved_at = created + timedelta(hours=resolution_hours) if status in ["Resolved", "Closed"] else None
        rows.append({
            "ticket_id": f"TKT-{10000+i}",
            "subject": subject,
            "description": f"User reported: {subject}. Department: {random.choice(DEPARTMENTS)}. Impact: {random.choice(['Single user', 'Multiple users', 'Department-wide', 'Company-wide'])}.",
            "category": cat,
            "priority": priority,
            "status": status,
            "created_at": created.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (created + timedelta(hours=random.randint(1, 12))).strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else "",
            "resolution_hours": resolution_hours if resolved_at else "",
            "assigned_agent": random.choice(AGENTS) if status != "Open" else "",
            "department": random.choice(DEPARTMENTS),
            "resolution_notes": random.choice(RESOLUTIONS) if resolved_at else "",
            "satisfaction_score": random.randint(1, 5) if resolved_at else "",
            "first_response_hours": random.randint(1, 8),
            "escalated": random.choice([True, False, False, False]),
            "sla_breached": random.choice([True, False, False, False, False]),
            "tenant_id": random.choice(["tenant_acme", "tenant_globex", "tenant_initech"]),
        })
    return pd.DataFrame(rows)

def generate_multilang_dataset(n=2000):
    rows = []
    lang_subjects = {
        "en": ["Cannot login", "System down", "Need software access", "Password reset", "Screen broken"],
        "de": ["Kann mich nicht anmelden", "System ausgefallen", "Software-Zugriff benötigt", "Passwort zurücksetzen", "Bildschirm defekt"],
        "fr": ["Impossible de se connecter", "Système en panne", "Besoin d'accès logiciel", "Réinitialiser le mot de passe", "Écran cassé"],
        "es": ["No puedo iniciar sesión", "Sistema caído", "Necesito acceso al software", "Restablecer contraseña", "Pantalla rota"],
        "pt": ["Não consigo fazer login", "Sistema fora do ar", "Preciso de acesso ao software", "Redefinir senha", "Tela quebrada"],
        "nl": ["Kan niet inloggen", "Systeem down", "Toegang tot software nodig", "Wachtwoord resetten", "Scherm kapot"],
    }
    for i in range(n):
        lang = random.choice(LANGUAGES)
        cat = random.choice(CATEGORIES)
        rows.append({
            "ticket_id": f"ML-{20000+i}",
            "subject": random.choice(lang_subjects[lang]),
            "body": f"Ticket submitted in {lang}. Category: {cat}. Priority escalated by user.",
            "language": lang,
            "category": cat,
            "priority": random.choice(PRIORITIES),
            "status": random.choice(STATUSES),
            "created_at": random_date(datetime(2023,1,1), datetime(2024,6,30)).strftime("%Y-%m-%d %H:%M:%S"),
            "tenant_id": random.choice(["tenant_acme", "tenant_globex", "tenant_initech"]),
        })
    return pd.DataFrame(rows)

def generate_timeseries_dataset(n=5000):
    start = datetime(2022, 1, 1)
    rows = []
    for i in range(n):
        ts = start + timedelta(hours=i*0.8)
        cat = random.choice(CATEGORIES)
        rows.append({
            "ticket_id": f"TS-{30000+i}",
            "created_at": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "category": cat,
            "priority": random.choices(PRIORITIES, weights=[30,40,20,10])[0],
            "resolved": random.choice([True, True, True, False]),
            "resolution_hours": random.randint(1, 96),
        })
    return pd.DataFrame(rows)

print("Generating datasets...")
df1 = generate_ticket_dataset(5000)
df1.to_csv("/home/claude/opsdesk/data/raw/all_tickets_processed_improved_v3.csv", index=False)
print(f"  ✓ all_tickets_processed_improved_v3.csv  ({len(df1)} rows)")

df2 = generate_ticket_dataset(3000)
df2.to_csv("/home/claude/opsdesk/data/raw/Support_Ticketing_Cleaned_Jan-Jul_2024.csv", index=False)
print(f"  ✓ Support_Ticketing_Cleaned_Jan-Jul_2024.csv ({len(df2)} rows)")

df3 = generate_multilang_dataset(2000)
df3.to_csv("/home/claude/opsdesk/data/raw/dataset-tickets-multi-lang-4-20k.csv", index=False)
print(f"  ✓ dataset-tickets-multi-lang-4-20k.csv ({len(df3)} rows)")

df4 = generate_ticket_dataset(800)
df4.to_csv("/home/claude/opsdesk/data/raw/customer_support_tickets_resolution.csv", index=False)
print(f"  ✓ customer_support_tickets_resolution.csv ({len(df4)} rows)")

df5 = generate_timeseries_dataset(5000)
df5.to_csv("/home/claude/opsdesk/data/raw/helpdesk_tickets_mendeley.csv", index=False)
print(f"  ✓ helpdesk_tickets_mendeley.csv ({len(df5)} rows)")

df6 = generate_ticket_dataset(1500)
df6.to_csv("/home/claude/opsdesk/data/raw/IT_helpdesk_synthetic_tickets.csv", index=False)
print(f"  ✓ IT_helpdesk_synthetic_tickets.csv ({len(df6)} rows)")

print("\nAll sample datasets generated successfully.")
