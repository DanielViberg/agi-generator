#!/usr/bin/env python3
"""Generate AGI XML for Skatteverket. Only parameter: period (YYYYMM)."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv, dotenv_values
except ImportError:
    print("pip install python-dotenv")
    sys.exit(1)


def get_config(env_file=".env"):
    load_dotenv(env_file)
    cfg = dotenv_values(dotenv_path=env_file)
    required = [
        "ORGANISATIONSNUMMER", "PROGRAMNAMN",
        "KONTAKT_NAMN", "KONTAKT_TELEFON", "KONTAKT_EPOST",
        "PERSONNUMMER", "LON", "SKATTEAVDRAG",
    ]
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        print(f"Missing in .env: {', '.join(missing)}")
        sys.exit(1)
    return cfg


def normalize_org(raw):
    """Strip dashes, prepend '16' if 10 digits (org nr), leave personnummer as-is."""
    s = raw.replace("-", "").replace(" ", "").strip()
    if len(s) == 10 and s.startswith(("5", "6", "7", "8", "9")):
        return "16" + s
    return s


def e(tag, text="", fk=None):
    """Build <agd:tag> element."""
    attr = f' faltkod="{str(fk).zfill(3)}"' if fk is not None else ""
    import xml.sax.saxutils as s
    return f"<agd:{tag}{attr}>{s.escape(str(text))}</agd:{tag}>"


def gen(period, cfg):
    org = normalize_org(cfg["ORGANISATIONSNUMMER"])
    personnr = cfg["PERSONNUMMER"].replace("-", "").replace(" ", "").strip()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    ns_i = "http://xmls.skatteverket.se/se/skatteverket/da/instans/schema/1.1"
    ns_k = "http://xmls.skatteverket.se/se/skatteverket/da/komponent/schema/1.1"
    ns_x = "http://www.w3.org/2001/XMLSchema-instance"

    root = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        f'<Skatteverket omrade="Arbetsgivardeklaration" '
        f'xmlns="{ns_i}" xmlns:agd="{ns_k}" xmlns:xsi="{ns_x}" '
        f'xsi:schemaLocation="{ns_i} http://xmls.skatteverket.se/se/skatteverket/da/arbetsgivardeklaration/arbetsgivardeklaration_1.1.xsd">'
    )

    # Avsandare
    root += (
        "<agd:Avsandare>"
        f"{e('Programnamn', cfg['PROGRAMNAMN'])}"
        f"{e('Organisationsnummer', org)}"
        "<agd:TekniskKontaktperson>"
        f"{e('Namn', cfg['KONTAKT_NAMN'])}"
        f"{e('Telefon', cfg['KONTAKT_TELEFON'])}"
        f"{e('Epostadress', cfg['KONTAKT_EPOST'])}"
        "</agd:TekniskKontaktperson>"
        f"{e('Skapad', now)}"
        "</agd:Avsandare>"
    )

    # Blankettgemensamt
    root += (
        "<agd:Blankettgemensamt>"
        "<agd:Arbetsgivare>"
        f"{e('AgRegistreradId', org)}"
        " <agd:Kontaktperson> "
        f"{e('Namn', cfg['KONTAKT_NAMN'])}"
        f" {e('Telefon', cfg['KONTAKT_TELEFON'])}"
        f" {e('Epostadress', cfg['KONTAKT_EPOST'])}"
        "</agd:Kontaktperson>"
        "</agd:Arbetsgivare>"
        "</agd:Blankettgemensamt>"
    )

    # HU - auto-calculate totals if not overridden
    lon = int(cfg["LON"])
    bil = int(cfg.get("BILFORMAN", "0") or "0")
    avg_underlag = lon + bil
    summa_avg = cfg.get("SUMMA_ARB_AVG_SLF", str(round(avg_underlag * 31.42 / 100)))
    summa_skatte = cfg.get("SUMMA_SKATTEAVDR", cfg["SKATTEAVDRAG"])
    root += (
        "<agd:Blankett>"
        "<agd:Arendeinformation>"
        f"{e('Arendeagare', org)}{e('Period', period)}"
        "</agd:Arendeinformation>"
        "<agd:Blankettinnehall><agd:HU>"
        "<agd:ArbetsgivareHUGROUP>"
        f"{e('AgRegistreradId', org, 201)}"
        "</agd:ArbetsgivareHUGROUP>"
        f"{e('RedovisningsPeriod', period, 6)}"
        f"{e('UlagFoU', cfg.get('ULAG_FOU', '0'), 470)}"
        f"{e('UlagRegionaltStod', cfg.get('ULAG_REGIONALT_STOD', '0'), 471)}"
        f"{e('AvdragFoU', cfg.get('AVDRAG_FOU', '0'), 475)}"
        f"{e('AvdragRegionaltStod', cfg.get('AVDRAG_REGIONALT_STOD', '0'), 476)}"
        f"{e('SummaArbAvgSlf', summa_avg, 487)}"
        f"{e('SummaSkatteavdr', summa_skatte, 497)}"
        "</agd:HU></agd:Blankettinnehall></agd:Blankett>"
    )

    # IU
    root += (
        "<agd:Blankett>"
        "<agd:Arendeinformation>"
        f"{e('Arendeagare', org)}{e('Period', period)}"
        "</agd:Arendeinformation>"
        "<agd:Blankettinnehall><agd:IU>"
        "<agd:ArbetsgivareIUGROUP>"
        f"{e('AgRegistreradId', org, 201)}"
        "</agd:ArbetsgivareIUGROUP>"
        "<agd:BetalningsmottagareIUGROUP>"
        "<agd:BetalningsmottagareIDChoice>"
       f"{e('BetalningsmottagarId', personnr, 215)}"
        "</agd:BetalningsmottagareIDChoice>"
        "</agd:BetalningsmottagareIUGROUP>"
        f"{e('AvdrPrelSkatt', cfg['SKATTEAVDRAG'], 1)}"
        f"{e('RedovisningsPeriod', period, 6)}"
        f"{e('AvrakningAvgiftsfriErs', cfg.get('AVRAKNING', '0'), 10)}"
        f"{e('KontantErsattningUlagAG', cfg['LON'], 11)}"
        f"{e('Tjanstepension', cfg.get('TJANSTEPENSION', '0'), 30)}"
        f"{e('SkatteplBilformanUlagAG', cfg.get('BILFORMAN', '0'), 13)}"
        f"{e('BetForDrivmVidBilformanUlagAG', cfg.get('BET_DRIVMEDEL', '0'), 98)}"
        f"{e('ArbetsplatsensGatuadress', cfg.get('ARBETSPLATS_GATA', ''), 245)}"
        f"{e('ArbetsplatsensOrt', cfg.get('ARBETSPLATS_ORT', ''), 246)}"
        f"{e('Specifikationsnummer', cfg.get('SPECIFIKATIONSNUMMER', '1'), 570)}"
        "</agd:IU></agd:Blankettinnehall></agd:Blankett>"
        "</Skatteverket>"
    )

    return root


def main():
    p = argparse.ArgumentParser(description="Generate AGI XML for Skatteverket")
    p.add_argument("period", help="Period YYYYMM, e.g. 202606")
    p.add_argument("-o", "--output", help="Output file (default: AGI_PERIOD_ORGNR.xml)")
    p.add_argument("--env-file", default=".env")
    a = p.parse_args()

    if len(a.period) != 6 or not a.period.isdigit():
        print("Period must be YYYYMM")
        sys.exit(1)

    cfg = get_config(a.env_file)
    org = normalize_org(cfg["ORGANISATIONSNUMMER"])

    xml = gen(a.period, cfg)

    out = a.output or f"AGI_{a.period}_{org}.xml"
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"Generated: {out}")


if __name__ == "__main__":
    main()
