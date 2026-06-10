# AGI Generator

Genererar XML för Arbetsgivardeklaration till Skatteverket.

## Setup

```bash
cp .env.example .env
```

Redigera `.env` med arbetsgivarens och den anställdes uppgifter.

## Användning

Enda parametern är redovisningsperioden (YYYYMM):

```bash
python3 generate_agi.py 202606
```

Genererar `AGI_202606_<orgnr>.xml`.

Valfri output-fil:
```bash
python3 generate_agi.py 202606 -o min_fil.xml
```

## Validering

Testa filen i Skatteverkets testtjänst:
https://sso.test.skatteverket.se/agd_tt/da_testtjanst_web/login.do?method=test
