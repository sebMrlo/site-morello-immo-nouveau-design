#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generateur de factures de commission d'honoraires - EI Morello Sebastien
Reproduit a l'identique le gabarit F-2026-06-xxx (geometrie extraite du PDF modele).
"""
from decimal import Decimal, ROUND_HALF_UP
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color

# ----------------------------------------------------------------- FONTS
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
REG, BOLD = "DejaVu", "DejaVu-Bold"

# ----------------------------------------------------------------- COLORS
NAVY      = Color(0.039216, 0.145098, 0.250980)
BOX_FILL  = Color(0.956863, 0.964706, 0.976471)
BOX_LINE  = Color(0.850980, 0.870588, 0.909804)
TBL_LINE  = Color(0.839216, 0.862745, 0.901961)
ROW_ALT   = Color(0.968627, 0.972549, 0.984314)
TOTAL_BG  = Color(0.909804, 0.933333, 0.964706)
BLACK     = Color(0, 0, 0)
WHITE     = Color(1, 1, 1)

PW, PH = 595.2756, 841.8898          # A4

# ----------------------------------------------------------------- HELPERS
def r2(x):
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def eur(x):
    """1825.75 -> '1 825,75 EUR' format francais avec espace milliers."""
    s = f"{r2(x):,.2f}".replace(",", " ").replace(".", ",")
    return s + " €"

def ht(ttc, taux=Decimal("1.2")):
    return r2(Decimal(str(ttc)) / taux)


class Facture:
    """Coordonnees en points, origine haut-gauche (converties pour reportlab)."""
    # colonnes du tableau (bornes verticales)
    COLS = [51.0, 107.7, 189.9, 255.1, 306.1, 334.5, 411.0, 481.9, 544.3]
    ALIGN = ["L", "L", "L", "L", "R", "R", "R", "L"]
    HEADERS = ["Date\nentrée", "Client", "Résidence", "Lot", "Nb",
               "Honoraires TTC", "Base HT", "Société"]
    PAD = 4.0
    ROW_H = 16.8
    TBL_TOP = 242.0
    HDR_H = 25.6

    def __init__(self, path, meta, emetteur, client, lignes, iban, bic):
        self.c = canvas.Canvas(path, pagesize=(PW, PH))
        self.meta, self.emetteur, self.client = meta, emetteur, client
        self.lignes, self.iban, self.bic = lignes, iban, bic

    # -- primitives (y = distance depuis le haut)
    def txt(self, x, y_top, s, font=REG, size=8.3, color=BLACK, align="L", width=None):
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        if align == "R":
            self.c.drawRightString(x, PH - y_top, s)
        elif align == "C":
            self.c.drawCentredString(x, PH - y_top, s)
        else:
            self.c.drawString(x, PH - y_top, s)

    def rect(self, x0, t0, x1, t1, fill):
        self.c.setFillColor(fill)
        self.c.rect(x0, PH - t1, x1 - x0, t1 - t0, stroke=0, fill=1)

    def line(self, x0, t0, x1, t1, color, lw):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(lw)
        self.c.line(x0, PH - t0, x1, PH - t1)

    def fit(self, s, size, maxw, font=REG):
        while size > 4.5 and pdfmetrics.stringWidth(s, font, size) > maxw:
            size -= 0.2
        return size

    # -- blocs
    def entete(self):
        m = self.meta
        self.txt(PW / 2, 61.02, "FACTURE", BOLD, 21.0, NAVY, "C")
        for i, s in enumerate([f"Facture n° {m['numero']}",
                               f"Date : {m['date']}",
                               f"Échéance : {m['echeance']}",
                               m["objet"]]):
            self.txt(45.7, 76.32 + i * 10, s)

    def parties(self):
        self.rect(39.7, 113.0, 555.6, 235.0, BOX_FILL)
        for a, b, c_, d in [(39.7, 113.0, 555.6, 113.0), (39.7, 235.0, 555.6, 235.0),
                            (39.7, 113.0, 39.7, 235.0), (555.6, 113.0, 555.6, 235.0)]:
            self.line(a, b, c_, d, BOX_LINE, 0.4)
        for x, lines in ((45.7, self.emetteur), (303.6, self.client)):
            y = 127.32
            for s in lines:
                if s is not None:
                    self.txt(x, y, s)
                y += 10

    def tableau(self):
        n = len(self.lignes)
        top, hh, rh = self.TBL_TOP, self.HDR_H, self.ROW_H
        hdr_bot = top + hh
        bot = hdr_bot + n * rh
        self.rect(self.COLS[0], top, self.COLS[-1], hdr_bot, NAVY)
        for i in range(n):
            if i % 2 == 1:
                self.rect(self.COLS[0], hdr_bot + i * rh, self.COLS[-1], hdr_bot + (i + 1) * rh, ROW_ALT)
        # bordures
        self.line(self.COLS[0], top, self.COLS[-1], top, TBL_LINE, 0.35)
        self.line(self.COLS[0], bot, self.COLS[-1], bot, TBL_LINE, 0.35)
        self.line(self.COLS[0], top, self.COLS[0], bot, TBL_LINE, 0.35)
        self.line(self.COLS[-1], top, self.COLS[-1], bot, TBL_LINE, 0.35)
        self.line(self.COLS[0], hdr_bot, self.COLS[-1], hdr_bot, TBL_LINE, 0.35)
        for i in range(1, n):
            y = hdr_bot + i * rh
            self.line(self.COLS[0], y, self.COLS[-1], y, TBL_LINE, 0.35)
        for x in self.COLS[1:-1]:
            self.line(x, top, x, bot, TBL_LINE, 0.35)
        # en-tetes
        for j, h in enumerate(self.HEADERS):
            parts = h.split("\n")
            base = 253.32 if len(parts) > 1 else 257.72
            for k, p in enumerate(parts):
                self.txt(self.COLS[j] + self.PAD, base + k * 8.8, p, BOLD, 7.3, WHITE)
        # corps
        for i, row in enumerate(self.lignes):
            base = 278.82 + i * rh
            for j, val in enumerate(row):
                maxw = self.COLS[j + 1] - self.COLS[j] - 2 * self.PAD
                sz = self.fit(val, 7.2, maxw)
                if self.ALIGN[j] == "R":
                    self.txt(self.COLS[j + 1] - self.PAD, base, val, REG, sz, BLACK, "R")
                else:
                    self.txt(self.COLS[j] + self.PAD, base, val, REG, sz)
        return bot

    def pied(self, tbl_bot, totaux):
        b = tbl_bot + 21.32
        self.txt(45.7, b, "MODALITÉS DE PAIEMENT")
        self.txt(45.7, b + 20, "Paiement par virement bancaire.")
        self.txt(45.7, b + 30, f"IBAN : {self.iban}")
        self.txt(45.7, b + 40, f"BIC : {self.bic}")
        t0 = tbl_bot + 13.0
        x0, xs, x1 = 317.8, 459.5, 555.9
        nrows = len(totaux)
        t1 = t0 + nrows * 18.0
        self.rect(x0, t1 - 18.0, x1, t1, TOTAL_BG)
        for a, y0, c_, y1 in [(x0, t0, x1, t0), (x0, t1, x1, t1), (x0, t0, x0, t1), (x1, t0, x1, t1)]:
            self.line(a, y0, c_, y1, TBL_LINE, 0.35)
        for i in range(1, nrows):
            self.line(x0, t0 + i * 18.0, x1, t0 + i * 18.0, TBL_LINE, 0.35)
        self.line(xs, t0, xs, t1, TBL_LINE, 0.35)
        for i, (lab, val) in enumerate(totaux):
            f = BOLD if i == nrows - 1 else REG
            base = t0 + 12.32 + i * 18.0
            self.txt(x0 + 5.0, base, lab, f)
            self.txt(xs + 5.0, base, val, f)

    def build(self, totaux):
        self.entete()
        self.parties()
        bot = self.tableau()
        self.pied(bot, totaux)
        self.c.setTitle(self.meta["numero"])
        self.c.save()


# ----------------------------------------------------------------- API
EMETTEUR = ["ÉMETTEUR", "Sébastien Morello", "EI Morello Sébastien",
            "345 Rue du jeu de mail des abbés", "34000 Montpellier", None,
            "Tél. : 06 42 55 40 60", "Email : sebastienmorello3@gmail.com",
            "SIRET : 517761748", "APE/NAF : 6831Z",
            "TVA : Franchise en base - article 293 B du CGI"]
CLIENTS = {
    "SNG": ["CLIENT", "SNG GROUPE", "1015 Rue du Lieutenant Parayre", "CS 40408",
            "13591 AIX EN PROVENCE CEDEX 3", None, "SIREN : 444 655 955"],
    "QUIETIS": ["CLIENT", "QUIETIS GESTION", "1015 Rue du Lieutenant Parayre", "CS 40408",
                "13591 AIX EN PROVENCE CEDEX 3", None, "SIREN : 810 183 723"],
}
CLIENT = CLIENTS["SNG"]          # retro-compatibilite
IBAN, BIC = "FR76 3000 4012 1900 0102 1080 981", "BNPAFRPPXXX"


def generer(path, numero, date, objet, entrees, societe, echeance="À réception", client=None):
    """entrees = [(date_entree, client, residence, lot, honoraires_ttc), ...]
    Le bloc CLIENT est choisi automatiquement selon `societe` (SNG / QUIETIS)."""
    client = client or CLIENTS.get(societe.upper(), CLIENTS["SNG"])
    lignes, total_ttc, total_ht = [], Decimal("0"), Decimal("0")
    for d, cl, res, lot, tt in entrees:
        h = ht(tt)
        total_ttc += r2(tt)
        total_ht += h
        lignes.append([d, cl, res, lot, "1", eur(tt), eur(h), societe])
    part = r2(total_ttc / Decimal("1.2") / 2)
    totaux = [("Total honoraires TTC", eur(total_ttc)),
              ("Total commission HT", eur(total_ht)),
              ("Part HT à 50 %", eur(part)),
              ("TVA", eur(0)),
              ("TOTAL À PAYER", eur(part))]
    Facture(path, {"numero": numero, "date": date, "echeance": echeance, "objet": objet},
            EMETTEUR, client, lignes, IBAN, BIC).build(totaux)
    return total_ttc, total_ht, part
