# 🚆 Simulatore di Sicurezza per Sportello di Biglietteria Ferroviaria (Stazione di Pompei)

Dimostratore didattico *Client-Server* sviluppato nell'ambito della Tesi di Laurea in **Ingegneria Informatica** per simulare i meccanismi di prevenzione, rilevamento (*Host-based Intrusion Detection*) e risposta a un attacco **Crypto-Ransomware** su una postazione fisica di biglietteria ferroviaria.

> **Nota metodologica e Disclaimer:**  
> Questo progetto è un simulatore didattico indipendente realizzato a scopo esclusivamente accademico e dimostrativo. Utilizza unicamente dati sintetici, tratte e tariffe pubbliche e librerie standard del linguaggio Python (`hashlib`, `sqlite3`, `http.server`), senza riprodurre né interagire con alcun software proprietario o infrastruttura reale.

---

## 🛡️ Paradigmi di Sicurezza Implementati

1. **Autenticazione Digitale & Role-Based Access Control (RBAC)**
   - Archiviazione sicura delle credenziali su database locale SQLite tramite digest crittografici **SHA-256** (nessuna password salvata in chiaro).
   - Separazione dei privilegi (*Least Privilege*) tra il ruolo **`OPERATORE DI SPORTELLO`** (abilitato all'emissione titoli) e il ruolo **`SUPERVISORE`** (unico profilo autorizzato al ripristino di emergenza da backup).

2. **Programmazione Sicura e Protezione del Database (Anti-SQL Injection & XSS)**
   - Ispezione preventiva degli input utente lato server per il rilevamento e il blocco di payload malevoli (`UNION SELECT`, `' OR 1=1`, `<script>`, `--`).
   - Interazione con il database relazionale SQLite esclusivamente tramite **Prepared Statements / Query Parametrizzate (`?`)**.

3. **Sentinella di Integrità File (HIDS SHA-256) e Contenimento Ransomware**
   - Calcolo in tempo reale dell'impronta crittografica **SHA-256** sul file tariffario locale della postazione (`tariffario_pompei.json`).
   - **Simulazione d'attacco:** alterando il file per riprodurre una cifratura ransomware, l'agente HIDS rileva il mismatch dell'hash SHA-256, **isola automaticamente il terminale dalla rete intranet**, inibisce l'emissione di biglietti corrotti e attiva a schermo la **Guida Operativa dei Primi 15 Minuti** per il personale di stazione.

4. **Accountability e Logging Forense**
   - Tracciamento in tempo reale di tutti gli eventi di sicurezza (accessi, emissioni PNR, tentativi di SQL Injection bloccati, violazioni RBAC, allarmi ransomware e ripristini) su console web e file di log (`hids_pompei.log`).

---

## 🔑 Credenziali di Test (RBAC)

| Ruolo | Utente | Password | Permessi |
| :--- | :--- | :--- | :--- |
| **Operatore di Sportello** | `puopolo_edda` | `@Autunno.2026!` | Emissione biglietti e monitoraggio integrità |
| **Supervisore / Admin** | `supervisore_fs` | `FsCert2026!` | Emissione biglietti + **Ripristino da Backup** post-attacco |

---

## 🐳 Avvio Rapido con Docker (Consigliato)

Il progetto è interamente containerizzato e non richiede dipendenze esterne.

```bash
# 1. Costruisci l'immagine Docker
docker build -t sportello-pompei .

# 2. Avvia il container sulla porta 8000
docker run --rm -p 8000:8000 --name simulatore-pompei sportello-pompei
```

Una volta avviato, apri il browser all'indirizzo: **[http://localhost:8000](http://localhost:8000)**

---

## 💻 Avvio Locale con Python 3 (Senza Docker)

Requisiti: **Python 3.9+** (usa esclusivamente la libreria standard, nessun pacchetto `pip` richiesto).

```bash
python3 server_pompei.py
```

Apri il browser all'indirizzo: **[http://localhost:8000](http://localhost:8000)**

---

## 👩‍💻 Autrice
**Edda Mariafrancesca Puopolo**  
*Corso di Laurea in Ingegneria Informatica*
