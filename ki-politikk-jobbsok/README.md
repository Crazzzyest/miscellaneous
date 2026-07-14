# KI-politikk jobbsøk – Norge

Oppgave: finn aktive (ikke utløpte) stillingsutlysninger relevante for en
KI-konsulent som søker innflytelse på KI-politikk i Norge.

## Status

Sist forsøkt: 2026-07-11. Denne økten kjørte i et miljø der nettverkspolicyen
blokkerer *all* utgående HTTPS til det åpne nettet (bekreftet ved at selv
`https://example.com` ga 403 på proxy-nivå). Ingen av sidene under kunne
derfor hentes. Dette er ikke sidenes bot-beskyttelse — det er sesjonens
egen nettverkspolicy.

For å fullføre: kjør denne oppgaven på nytt i et miljø/sesjon med åpen
nettverkstilgang (se https://code.claude.com/docs/en/claude-code-on-the-web
for hvordan nettverkspolicy velges), og bruk WebFetch (ikke websøk) på hver
URL under.

## Kilder å hente (WebFetch, ikke websøk)

| Organisasjon | URL |
|---|---|
| Datatilsynet | https://www.datatilsynet.no/om-datatilsynet/ledig-stilling-og-status/ |
| Digdir | https://www.digdir.no/digdir/ledige-stillinger-i-digdir/705 |
| Nkom | https://nkom.no/karriere/ledige-stillinger |
| NUPI | https://www.nupi.no/om-nupi/ledige-stillinger |
| Digitaliserings- og forvaltningsdepartementet | https://www.regjeringen.no/no/aktuelt/stillinger/id3021468/ |

## WebFetch-prompt (bruk denne for hver URL)

> List all currently open/vacant job positions (ledige stillinger) with their
> title and application deadline (søknadsfrist). For each, give the exact
> deadline date if shown. Ignore expired positions. If none are listed, say so.

## Sluttleveranse (format)

For hver side: list kun stillinger med aktiv søknadsfrist. Hvis ingen
aktive stillinger for en organisasjon: skriv "Ingen aktive stillinger".

Tabell:

| Stillingstittel | Organisasjon | Søknadsfrist |
|---|---|---|

Avslutt med én linje: totalt antall aktive stillinger på tvers av alle fem
organisasjoner.
