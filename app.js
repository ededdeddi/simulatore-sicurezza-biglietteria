// === APP.JS: COLLEGA L'INTERFACCIA HTML ALLA SENTINELLA PYTHON ===

function aggiornaSchermata(dati) {
    // 1. Aggiorna operatore e Ruolo nella barra in alto
    const badgeUtente = document.getElementById("info-operatore");
    if (dati.nome_completo) {
        badgeUtente.textContent = `Operatore: ${dati.nome_completo} (${dati.ruolo})`;
    } else {
        badgeUtente.textContent = "Operatore: Non autenticato";
    }
    // 2. Aggiorna gli Hash SHA-256 nel pannello HIDS
    document.getElementById("hash-ufficiale").textContent = dati.hash_ufficiale;
    document.getElementById("hash-attuale").textContent = dati.hash_attuale;

    // 3. Controlla se il file tariffario_pompei.json è INTEGRO o SOTTO ATTACCO
    const badgeRete = document.getElementById("badge-rete");
    const statoIntegrita = document.getElementById("stato-integrita");
    const box15Min = document.getElementById("box-protocollo-15min");

    if (dati.integro) {
        badgeRete.textContent = "RETE INTRANET AZIENDALE: OPERATIVA";
        badgeRete.className = "badge-verde";
        statoIntegrita.textContent = "[OK] File Integro — Nessuna anomalia rilevata";
        statoIntegrita.style.color = "#15803d";
        box15Min.className = "allerta-nascosta"; // Nasconde SOLO la Guida Operativa
    } else {
        badgeRete.textContent = "ALLARME RANSOMWARE: POSTAZIONE ISOLATA";
        badgeRete.className = "badge-rosso";
        statoIntegrita.textContent = "[CRITICO] VIOLAZIONE SHA-256! File locale cifrato!";
        statoIntegrita.style.color = "#dc2626";
        box15Min.className = "allerta-attiva"; // Mostra la Guida Operativa in caso di attacco
    }
    // 4. Aggiorna la console nera dei Log di sicurezza (HIDS)
    if (dati.logs) {
        document.getElementById("console-log").textContent = dati.logs.join("\n");
    }
}
// Funzione di utilità per inviare richieste POST a Python
async function inviaComando(url, payload = {}) {
    const risposta = await fetch(url,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
    const dati = await risposta.json();
    aggiornaSchermata(dati);
    return dati;
}
// 1. Bottone LOGIN (RBAC + Anti-SQLi)
document.getElementById("btn-login").addEventListener("click", async () => {
    const username = document.getElementById("input-username").value;
    const password = document.getElementById("input-password").value;
    const esito = await inviaComando("/api/login",
        {
            username, password
        });
    document.getElementById("messaggio-login").textContent = esito.msg;
});

// 2. Bottone EMETTI BIGLIETTO (Controllo Integrità + Anti-SQLi)
document.getElementById("btn-emetti").addEventListener("click", async () => {
    const tratta = document.getElementById("select-tratta").value;
    const passeggero = document.getElementById("input-passeggero").value;
    const esito = await inviaComando("/api/emetti",
        {
            tratta, passeggero
        });
    const box = document.getElementById("box-biglietto-emesso");

    if (esito.ok) {
        box.innerHTML = `<strong>TITOLO EMESSO CON SUCCESSO</strong><br>
         Codice PNR: <code>${esito.pnr}</code> | Treno / Tratta: ${esito.tratta}<br>
         Viaggiatore: ${esito.passeggero} | Orario: ${esito.orario}`;
    } else {
        box.innerHTML = `<strong style="color:#dc2626;">${esito.msg
            }</strong>`;
    }
});

// 3. Bottone SIMULA ATTACCO RANSOMWARE
document.getElementById("btn-simula-ransomware").addEventListener("click", async () => {
    await inviaComando("/api/simula_ransomware");
    document.getElementById("box-biglietto-emesso").innerHTML =
        `<strong style="color:#dc2626;">TERMINALE ISOLATO DALLA RETE INTRANET: Emissione locale bloccata.</strong>`;
});

// 4. Bottone RIPRISTINA DA BACKUP (Consentito solo da Amministratore)
document.getElementById("btn-ripristina-backup").addEventListener("click", async () => {
    const esito = await inviaComando("/api/ripristina_backup");
    if (esito.ok) {
        document.getElementById("box-biglietto-emesso").innerHTML =
            `<strong style="color:#15803d;">TERMINALE RIPRISTINATO DALL'AMMINISTRATORE: Sportello di Pompei nuovamente abilitato all'emissione.</strong>`;
    }
    alert(esito.msg);
});

// Carica lo stato iniziale appena si apre la pagina
fetch("/api/stato").then(r => r.json()).then(aggiornaSchermata);