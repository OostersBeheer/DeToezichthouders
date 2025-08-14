# Toezichthouders Jobboard — v3 (categorie-filter + Over ons)

MVP jobboard met:
- Extra velden: Bedrijf, Locatie, Startdatum, Duur, Aantal uur, Tarief, Omschrijving
- **Categorieën** (selectie bij plaatsen, filter voor bezoekers op de homepage)
- **Over ons** pagina (`/over-ons`)
- Reacties + optionele CV-upload (PDF, max 5MB)
- Eenvoudige admin via `?pw=` (CSRF-beveiligd)

## Lokale installatie

```
python -m venv .venv
# Mac/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Stel ADMIN_PASSWORD en SECRET_KEY in
flask --app app.py init-db
python app.py
```

Open: http://127.0.0.1:5000  
Admin: `/admin?pw=JOUW_WACHTWOORD`  
Over ons: `/over-ons`

> Tip: Categorieën aanpassen? Pas de lijst `CATEGORIES` aan bovenin `app.py`.

## Deploy op Render (via GitHub)

1. Zet deze map in een GitHub-repository (upload via web is prima).
2. In Render: **New Web Service → Connect GitHub → kies je repo**.
3. **Environment**: Python 3  
   **Build Command**: `pip install -r requirements.txt`  
   **Start Command**: `python app.py` of `gunicorn app:app`
4. **Environment Variables**:  
   `ADMIN_PASSWORD` en `SECRET_KEY` instellen.
5. Deploy. Je krijgt een URL als `https://jouwsite.onrender.com`.

## Opmerkingen / uitbreiden

- Zoek- en filteropties uitbreiden (locatie, startdatum, tarief range)
- E-mailnotificaties bij nieuwe reacties
- Echte admin-login i.p.v. `?pw=`
- Contactpagina, privacy/AVG, cookie-banner
- Bestanden extern opslaan (S3) voor schaalbaarheid
