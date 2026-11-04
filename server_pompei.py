import hashlib
import datetime
import sqlite3
import random
import string
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Nome del file locale dello sportello di Pompei da monitorare
FILE_TARIFFARIO = "tariffario_pompei.json"

# Contenuto originale integro (funge da Copia di Backup Sicura e Isolata / Offline)
with open(FILE_TARIFFARIO, "r", encoding="utf-8") as f:
    BACKUP_PULITO = f.read()


def calcola_hash_sha256(percorso_file):
    """
    Calcola l'impronta crittografica SHA-256 (64 caratteri esadecimali) del file.
    Rif. Corso: Dispensa 5 (Funzioni Hash Sicure) e Dispensa 18 (Host-based Scanner).
    """
    calcolatore = hashlib.sha256()
    with open(percorso_file, "rb") as file_letto:
        byte_file = file_letto.read()
    calcolatore.update(byte_file)
    return calcolatore.hexdigest()


# Calcoliamo all'avvio l'impronta SHA-256 ufficiale del file sano
HASH_UFFICIALE_SANO = calcola_hash_sha256(FILE_TARIFFARIO)


def verifica_integrita_tariffario():
    """
    Confronta l'Hash attuale sul disco con l'Hash ufficiale sano.
    Restituisce (True, hash_attuale) se integro, (False, hash_attuale) se manomesso/cifrato.
    """
    hash_attuale = calcola_hash_sha256(FILE_TARIFFARIO)
    integro = (hash_attuale == HASH_UFFICIALE_SANO)
    return integro, hash_attuale


def simula_cifratura_ransomware():
    """
    Simula l'azione di un Crypto-Ransomware (Dispensa 14 - Data Encryption):
    sovrascrive il file tariffario_pompei.json con un blocco cifrato simulato.
    """
    contenuto_cifrato = (
        "--- [RANSOMWARE ENCRYPTED PAYLOAD - ALGORITMO IBRIDO] ---\n"
        "DATI_CIFRATI_HEX: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08\n"
        "NOTA_RISCATTO: I file della postazione POMPEI_SPORTELLO_01 sono stati cifrati.\n"
    )
    with open(FILE_TARIFFARIO, "w", encoding="utf-8") as f:
        f.write(contenuto_cifrato)


def ripristina_tariffario_da_backup():
    """
    Ripristina il file tariffario_pompei.json dalla copia di backup isolata.
    """
    with open(FILE_TARIFFARIO, "w", encoding="utf-8") as f:
        f.write(BACKUP_PULITO)

# === PEZZO 2: DATABASE SQLITE, PASSWORD HASHATE, RBAC E ANTI-SQLi ===

DB_FILE = "sportello_pompei.db"


def calcola_hash_password(testo_password):
    """Trasforma una password in chiaro nella sua impronta SHA-256 (Dispensa 9)."""
    return hashlib.sha256(testo_password.encode("utf-8")).hexdigest()


def inizializza_database():
    """Crea le tabelle 'operatori' e 'biglietti_emessi' con Nome Completo e Ruolo."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Ricrea la tabella operatori aggiornata con la colonna nome_completo
    cur.execute("DROP TABLE IF EXISTS operatori")
    cur.execute("""
        CREATE TABLE operatori (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            nome_completo TEXT NOT NULL,
            ruolo TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS biglietti_emessi (
            pnr TEXT PRIMARY KEY,
            tratta TEXT NOT NULL,
            passeggero TEXT NOT NULL,
            operatore TEXT NOT NULL,
            orario TEXT NOT NULL
        )
    """)

    # QUI PUOI CAMBIARE "supervisore_fs" CON L'USERNAME CHE PREFERISCI PER IL SUPERVISORE
    utenti_iniziali = [
        ("puopolo_edda",   calcola_hash_password("@Autunno.2026!"), "Edda Mariafrancesca Puopolo", "OPERATORE DI SPORTELLO"),
        ("supervisore_fs", calcola_hash_password("FsCert2026!"),    "Supervisore",                 "SUPERVISORE")
    ]
    cur.executemany(
        "INSERT INTO operatori (username, password_hash, nome_completo, ruolo) VALUES (?, ?, ?, ?)",
        utenti_iniziali
    )

    conn.commit()
    conn.close()


def autentica_utente(username, password_inserita):
    """Restituisce (nome_completo, ruolo) se le credenziali sono valide, altrimenti (None, None)."""
    hash_inserito = calcola_hash_password(password_inserita)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT nome_completo, ruolo FROM operatori WHERE username = ? AND password_hash = ?",
        (username, hash_inserito)
    )
    riga = cur.fetchone()
    conn.close()
    return (riga[0], riga[1]) if riga else (None, None)


def input_contiene_attacco(testo):
    """Intercetta pattern tipici di SQL Injection o Cross-Site Scripting (XSS)."""
    pattern_pericolosi = ["'", "\"", ";", "--", "/*", "*/", "<script", " or ", "drop ", "union ", "select "]
    testo_minuscolo = testo.lower()
    for p in pattern_pericolosi:
        if p in testo_minuscolo:
            return True
    return False


def registra_biglietto_db(tratta, passeggero, operatore):
    """Genera un codice PNR di 5 caratteri alfanumerici maiuscoli (es. A7K9M)."""
    caratteri_pnr = string.ascii_uppercase + string.digits
    codice_pnr = "".join(random.choices(caratteri_pnr, k=5))
    orario = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO biglietti_emessi (pnr, tratta, passeggero, operatore, orario) VALUES (?, ?, ?, ?, ?)",
        (codice_pnr, tratta, passeggero, operatore, orario)
    )
    conn.commit()
    conn.close()
    return codice_pnr, orario


# === PEZZO 3: REGISTRO LOG HIDS E SERVER LOCALE PER LA PAGINA HTML ===

SESSIONE_CORRENTE = {"username": None, "nome_completo": None, "ruolo": None}
REGISTRO_LOG = []


def scrivi_log(livello, messaggio):
    orario = datetime.datetime.now().strftime("%H:%M:%S")
    riga = f"[{orario}] [{livello}] {messaggio}"
    REGISTRO_LOG.append(riga)
    with open("hids_pompei.log", "a", encoding="utf-8") as f:
        f.write(riga + "\n")


class GestoreSportelloPompei(SimpleHTTPRequestHandler):

    def invia_json(self, dati):
        integro, hash_attuale = verifica_integrita_tariffario()
        dati["integro"] = integro
        dati["hash_ufficiale"] = HASH_UFFICIALE_SANO
        dati["hash_attuale"] = hash_attuale
        dati["utente"] = SESSIONE_CORRENTE["username"]
        dati["nome_completo"] = SESSIONE_CORRENTE["nome_completo"]
        dati["ruolo"] = SESSIONE_CORRENTE["ruolo"]
        dati["logs"] = REGISTRO_LOG[-12:]

        corpo = json.dumps(dati).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path == "/api/stato":
            self.invia_json({"ok": True})
        else:
            super().do_GET()

    def do_POST(self):
        lunghezza = int(self.headers.get("Content-Length", 0))
        dati_input = json.loads(self.rfile.read(lunghezza).decode("utf-8")) if lunghezza > 0 else {}

        # 1. AZIONE: LOGIN OPERATORE
        if self.path == "/api/login":
            user = dati_input.get("username", "").strip()
            pwd = dati_input.get("password", "")
            if input_contiene_attacco(user):
                scrivi_log("ALLARME-SQLi", f"Tentativo di SQL Injection bloccato sul campo Login: {user}")
                return self.invia_json({"ok": False, "msg": "Input bloccato: rilevati caratteri non consentiti (Anti-SQLi)."})

            nome_completo, ruolo = autentica_utente(user, pwd)
            if ruolo:
                SESSIONE_CORRENTE["username"] = user
                SESSIONE_CORRENTE["nome_completo"] = nome_completo
                SESSIONE_CORRENTE["ruolo"] = ruolo
                scrivi_log("AUTH-RBAC", f"Accesso autorizzato per '{nome_completo}' ({ruolo}).")
                saluto = "Benvenuta" if user == "puopolo_edda" else "Benvenuto/a"
                return self.invia_json({"ok": True, "msg": f"{saluto} {nome_completo} ({ruolo})."})
            else:
                scrivi_log("AUTH-FAIL", f"Credenziali errate per l'utente '{user}'.")
                return self.invia_json({"ok": False, "msg": "Credenziali non valide."})

        # 2. AZIONE: EMISSIONE BIGLIETTO
        elif self.path == "/api/emetti":
            integro, _ = verifica_integrita_tariffario()
            if not integro:
                scrivi_log("BLOCCO-RETE", "Emissione negata: postazione isolata per violazione integrità SHA-256!")
                return self.invia_json({"ok": False, "msg": "BLOCCO SICUREZZA: Postazione isolata! Seguire procedura Primi 15 Minuti."})

            if not SESSIONE_CORRENTE["username"]:
                return self.invia_json({"ok": False, "msg": "Effettuare prima il login operatore."})

            tratta = dati_input.get("tratta", "")
            passeggero = dati_input.get("passeggero", "").strip()
            if not passeggero:
                return self.invia_json({"ok": False, "msg": "Inserire il nominativo del viaggiatore."})

            if input_contiene_attacco(passeggero):
                scrivi_log("ALLARME-SQLi", f"Bloccato payload malevolo nel campo Viaggiatore: {passeggero}")
                return self.invia_json({"ok": False, "msg": "ALLARME SICUREZZA SOFTWARE: Rilevato tentativo di Injection nell'input!"})

            pnr, orario = registra_biglietto_db(tratta, passeggero, SESSIONE_CORRENTE["nome_completo"])
            scrivi_log("EMISSIONE-OK", f"Emesso PNR {pnr} ({tratta}) da {SESSIONE_CORRENTE['nome_completo']}.")
            return self.invia_json({"ok": True, "pnr": pnr, "tratta": tratta, "passeggero": passeggero, "orario": orario})

        # 3. AZIONE: SIMULA ATTACCO RANSOMWARE
        elif self.path == "/api/simula_ransomware":
            simula_cifratura_ransomware()
            scrivi_log("CRITICAL-HIDS", "Violazione Hash SHA-256 su tariffario_pompei.json! Rilevata cifratura Ransomware.")
            scrivi_log("ISOLAMENTO-RETE", "Disconnessione automatica dalla Rete Intranet attivata sulla Postazione n° 1 di Pompei.")
            return self.invia_json({"ok": True})

        # 4. AZIONE: RIPRISTINA DA BACKUP
        elif self.path == "/api/ripristina_backup":
            if SESSIONE_CORRENTE["ruolo"] != "SUPERVISORE":
                scrivi_log("RBAC-NEGATO", f"Utente '{SESSIONE_CORRENTE['nome_completo']}' ({SESSIONE_CORRENTE['ruolo']}) non autorizzato al ripristino.")
                return self.invia_json({"ok": False, "msg": "ACCESSO NEGATO: Operazione consentita solo al profilo Supervisore / Amministratore!"})

            ripristina_tariffario_da_backup()
            scrivi_log("RECOVERY-OK", f"Backup sano ripristinato da '{SESSIONE_CORRENTE['nome_completo']}'. Hash SHA-256 verificato. Postazione riattivata.")
            return self.invia_json({"ok": True, "msg": "Backup ripristinato con successo. Integrità SHA-256 ristabilita!"})


if __name__ == "__main__":
    inizializza_database()
    scrivi_log("AVVIO-HIDS", f"Sentinella attiva su Pompei Postazione 1. Hash SHA-256 originale: {HASH_UFFICIALE_SANO[:16]}...")
    print("=================================================================")
    print(" SIMULATORE SPORTELLO BIGLIETTERIA POMPEI ATTIVO!")
    print(" Apri il browser all'indirizzo: http://localhost:8000")
    print("=================================================================")
    HTTPServer(("0.0.0.0", 8000), GestoreSportelloPompei).serve_forever()