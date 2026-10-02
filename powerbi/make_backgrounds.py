"""
Generates the dark-premium page backgrounds for the Power BI dashboard.

Each image is a 1280x720 layout (rendered at 2x for sharpness) containing the
sidebar navigation, page header, KPI tiles and chart panels with their titles.
In Power BI you set the image as the page background and place transparent
visuals inside the panels. Coordinates in LAYOUT are in 1280x720 units, the
same units Power BI shows under Format > General > Properties > Position/Size.

Run:  python powerbi/make_backgrounds.py
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(__file__).parent / "backgrounds"
OUT.mkdir(exist_ok=True)
S = 2                      # render scale
W, H = 1280, 720
FONTS = Path("C:/Windows/Fonts")

# ---- design tokens ---------------------------------------------------------
BG = (7, 13, 26)
SIDEBAR = (10, 18, 34)
PANEL = (14, 23, 42)
PANEL_BORDER = (30, 44, 70)
TEXT = (241, 245, 249)
MUTED = (124, 139, 165)
SUBTLE = (82, 97, 124)
TEAL, SKY, VIOLET, AMBER, ROSE, GREEN = (45, 212, 191), (56, 189, 248), (167, 139, 250), (245, 158, 11), (251, 113, 133), (74, 222, 128)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), int(size * S))

F_BOLD, F_SEMI, F_REG, F_LIGHT = "segoeuib.ttf", "seguisb.ttf", "segoeui.ttf", "segoeuil.ttf"

NAV = ["Overview", "Segments", "Churn Risk", "Cohorts", "Forecast"]

# ---- page specs -------------------------------------------------------------
# kpis: (label, accent, baked_value or None)   panels: (x1, y1, x2, y2, title, kind, content)
LAYOUT = [
    dict(file="01_overview", nav=0, title="Executive Overview",
         subtitle="How is the business performing?  ·  Dec 2009 – Dec 2011  ·  1.0M transactions",
         slicers=2,
         kpis=[("TOTAL REVENUE", TEAL, None), ("ORDERS", SKY, None), ("ACTIVE CUSTOMERS", VIOLET, None),
               ("AVG ORDER VALUE", AMBER, None), ("REVENUE YoY", ROSE, None)],
         panels=[(190, 200, 850, 455, "MONTHLY REVENUE  ·  THIS YEAR VS LAST YEAR", "visual", None),
                 (870, 200, 1260, 455, "TOP 8 MARKETS  ·  EXCL. UK", "visual", None),
                 (190, 470, 620, 700, "ORDERS BY WEEKDAY", "visual", None),
                 (640, 470, 1260, 700, "KEY INSIGHTS", "text", [
                     (TEAL, "Top 20% of customers generate 77% of revenue: high concentration risk."),
                     (AMBER, "Revenue peaks Sep–Nov every year (gift season); Nov ≈ 2× spring months."),
                     (SKY, "UK is 85% of revenue; Ireland, Netherlands and Germany lead overseas."),
                     (VIOLET, "Weekday, office-hours ordering: a B2B wholesale customer base.")])]),
    dict(file="02_segments", nav=1, title="Customer Segments  ·  RFM",
         subtitle="Who are our customers, and who matters most?  ·  Recency · Frequency · Monetary",
         slicers=1,
         kpis=[("CUSTOMERS", TEAL, None), ("REPEAT CUSTOMER RATE", SKY, None), ("CHAMPIONS' SHARE OF REVENUE", AMBER, None),
               ("REVENUE AT RISK (LAPSING)", ROSE, None)],
         panels=[(190, 200, 800, 455, "SHARE OF CUSTOMERS VS SHARE OF REVENUE BY SEGMENT", "visual", None),
                 (820, 200, 1260, 455, "REVENUE BY SEGMENT", "visual", None),
                 (190, 470, 560, 700, "R × F GRID  ·  CUSTOMERS PER CELL", "visual", None),
                 (580, 470, 1260, 700, "SEGMENT PLAYBOOK  ·  RECOMMENDED ACTIONS", "visual", None)]),
    dict(file="03_churn", nav=2, title="Churn Risk",
         subtitle="Who is likely to stop buying in the next 90 days, and how much revenue is at stake?",
         slicers=1,
         kpis=[("REVENUE AT RISK · NEXT QTR", ROSE, None), ("HIGH-RISK CUSTOMERS", AMBER, None),
               ("AVG CHURN PROBABILITY", VIOLET, None), ("MODEL ROC-AUC (OUT-OF-TIME)", TEAL, "0.77")],
         panels=[(190, 200, 800, 455, "CUSTOMER VALUE VS CHURN RISK", "visual", None),
                 (820, 200, 1260, 455, "CUSTOMERS BY RISK BAND", "visual", None),
                 (190, 470, 850, 700, "PRIORITY CALL LIST  ·  TOP 20 BY REVENUE AT RISK", "visual", None),
                 (870, 470, 1260, 700, "REVENUE AT RISK BY SEGMENT", "visual", None)]),
    dict(file="04_cohorts", nav=3, title="Cohort Retention",
         subtitle="Do new customers come back?  ·  % of each acquisition cohort active N months later",
         slicers=0,
         kpis=[("MONTH-1 RETENTION", TEAL, None), ("MONTH-3 RETENTION", SKY, None),
               ("MONTH-12 RETENTION", VIOLET, None), ("ONE-TIME BUYERS", ROSE, None)],
         panels=[(190, 200, 880, 700, "RETENTION HEATMAP  ·  COHORT × MONTHS SINCE FIRST PURCHASE", "visual", None),
                 (900, 200, 1260, 455, "AVERAGE RETENTION CURVE", "visual", None),
                 (900, 470, 1260, 700, "WHAT IT MEANS", "text", [
                     (ROSE, "The biggest drop happens right after the first order: only ~21% return next month."),
                     (TEAL, "Customers who stay past month 3 tend to stay: retention flattens at ~18–20%."),
                     (AMBER, "Repeat buyers spend 11× more: a 2nd-purchase journey is the top lever.")])]),
    dict(file="05_forecast", nav=4, title="Revenue Forecast",
         subtitle="What revenue should we expect next quarter?  ·  Weekly forecast with 80% / 95% ranges",
         slicers=0,
         kpis=[("FORECAST · NEXT 13 WEEKS", TEAL, None), ("LOW CASE (80%)", AMBER, None), ("HIGH CASE (80%)", SKY, None),
               ("BACKTEST ERROR (WAPE)", VIOLET, "12.1%"), ("FORECAST BIAS", GREEN, "−0.9%")],
         panels=[(190, 200, 1260, 505, "WEEKLY REVENUE  ·  ACTUAL, BACKTEST AND FORECAST", "visual", None),
                 (190, 520, 700, 700, "BACKTEST LEADERBOARD  ·  UNSEEN SEP–DEC 2011", "table", [
                     ("Method", "WAPE", "Bias"),
                     ("Ensemble (chosen)", "12.1%", "−0.9%"),
                     ("Harmonic regression", "12.8%", "−4.6%"),
                     ("Seasonal naive × growth", "15.2%", "+2.8%"),
                     ("Naive (last week)", "47.3%", "−47.3%")]),
                 (720, 520, 1260, 700, "HOW IT WORKS", "text", [
                     (TEAL, "Trend + yearly Fourier seasonality + Christmas-shutdown flag (OLS), K chosen by AIC."),
                     (AMBER, "Averaged with 'same week last year × growth' for a robust ensemble."),
                     (VIOLET, "Tested on a quarter the model never saw before being trusted.")])]),
]


# ---- drawing helpers --------------------------------------------------------
def s(*v):
    return [int(round(x * S)) for x in v]


def background():
    """Deep navy base with two soft colour glows."""
    y, x = np.mgrid[0:H * S, 0:W * S].astype(np.float32)
    img = np.zeros((H * S, W * S, 3), np.float32) + np.array(BG, np.float32)
    for (cx, cy, r, col, strength) in [(1150, 40, 520, TEAL, 0.10), (300, 760, 560, VIOLET, 0.09)]:
        d = np.sqrt((x - cx * S) ** 2 + (y - cy * S) ** 2) / (r * S)
        a = np.clip(1 - d, 0, 1) ** 2 * strength
        img += a[..., None] * (np.array(col, np.float32) - img)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert("RGBA")


def glow(base, box, color, radius=10, alpha=140, blur=14):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(s(*box), radius=radius * S, fill=color + (alpha,))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur * S)))


def panel(img, x1, y1, x2, y2, radius=14):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(s(x1, y1, x2, y2), radius=radius * S, fill=PANEL + (235,), outline=PANEL_BORDER + (255,), width=S)
    # faint top highlight line
    d.line(s(x1 + radius, y1 + 1, x2 - radius, y1 + 1), fill=(255, 255, 255, 18), width=S)
    img.alpha_composite(layer)


def text(d, xy, t, f, fill, anchor="la", spacing=0):
    d.text(s(*xy), t, font=f, fill=fill, anchor=anchor, spacing=spacing)


def tracked(d, xy, t, f, fill, tracking=1.2):
    """Letter-spaced uppercase label."""
    x, y = xy
    for ch in t:
        d.text(s(x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) / S + tracking


def wrap(t, f, width):
    words, lines, cur = t.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if f.getlength(test) / S <= width:
            cur = test
        else:
            lines.append(cur); cur = w
    return lines + [cur]


# ---- page renderer ----------------------------------------------------------
def render(spec):
    img = background()
    d = ImageDraw.Draw(img)

    # sidebar
    side = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(side).rectangle(s(0, 0, 170, H), fill=SIDEBAR + (245,))
    ImageDraw.Draw(side).line(s(170, 0, 170, H), fill=PANEL_BORDER + (255,), width=S)
    img.alpha_composite(side)
    d = ImageDraw.Draw(img)

    # logo mark
    glow(img, (20, 26, 54, 60), TEAL, radius=9, alpha=120, blur=8)
    d = ImageDraw.Draw(img)
    grad = Image.new("RGBA", s(34, 34)[::-1][::-1], (0, 0, 0, 0))
    gw = grad.size[0]
    g = np.linspace(0, 1, gw)[None, :, None]
    arr = (np.array(TEAL) * (1 - g) + np.array(SKY) * g) * np.ones((gw, 1, 1))
    grad = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    mask = Image.new("L", grad.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, gw - 1, gw - 1), radius=9 * S, fill=255)
    img.paste(grad, s(20, 26), mask)
    d = ImageDraw.Draw(img)
    text(d, (37, 43), "CA", font(F_BOLD, 13), BG, anchor="mm")
    text(d, (64, 25), "Customer", font(F_BOLD, 14), TEXT)
    text(d, (64, 43), "Analytics", font(F_LIGHT, 14), TEXT)

    tracked(d, (22, 104), "DASHBOARD", font(F_SEMI, 8.5), SUBTLE, 1.6)
    for i, name in enumerate(NAV):
        y = 124 + i * 46
        if i == spec["nav"]:
            hl = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(hl).rounded_rectangle(s(12, y, 158, y + 36), radius=9 * S, fill=(22, 36, 62, 255))
            img.alpha_composite(hl)
            glow(img, (12, y + 8, 16, y + 28), TEAL, radius=2, alpha=200, blur=5)
            d = ImageDraw.Draw(img)
            d.rounded_rectangle(s(12, y + 8, 15, y + 28), radius=2 * S, fill=TEAL)
            col, f = TEXT, font(F_SEMI, 12.5)
        else:
            col, f = MUTED, font(F_REG, 12.5)
        text(d, (28, y + 18), f"{i + 1:02d}", font(F_SEMI, 10), TEAL if i == spec["nav"] else SUBTLE, anchor="lm")
        text(d, (52, y + 18), name, f, col, anchor="lm")

    tracked(d, (22, 612), "DATA", font(F_SEMI, 8.5), SUBTLE, 1.6)
    for j, line in enumerate(["UCI Online Retail II", "1.0M transactions", "Dec 2009 – Dec 2011", "Python · SQL · Power BI"]):
        text(d, (22, 630 + j * 16), line, font(F_REG, 10), MUTED if j < 3 else SUBTLE)

    # header
    text(d, (190, 20), spec["title"], font(F_BOLD, 25), TEXT)
    text(d, (191, 60), spec["subtitle"], font(F_REG, 11.5), MUTED)
    for k in range(spec["slicers"]):           # slicer slots, right-aligned
        x2 = 1260 - k * 170
        panel(img, x2 - 155, 26, x2, 64, radius=10)
    d = ImageDraw.Draw(img)

    # KPI tiles
    kpis = spec["kpis"]
    gap, x0, x1 = 16, 190, 1260
    kw = (x1 - x0 - gap * (len(kpis) - 1)) / len(kpis)
    for i, (label, col, baked) in enumerate(kpis):
        kx = x0 + i * (kw + gap)
        glow(img, (kx + 10, 180, kx + kw - 10, 186), col, radius=3, alpha=90, blur=10)
        panel(img, kx, 92, kx + kw, 184, radius=12)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle(s(kx + 14, 180, kx + kw - 14, 183), radius=2 * S, fill=col)   # accent underline
        d.ellipse(s(kx + 16, 106, kx + 23, 113), fill=col)
        tracked(d, (kx + 30, 103), label, font(F_SEMI, 8.5), MUTED, 1.1)
        if baked:
            text(d, (kx + 16, 152), baked, font(F_BOLD, 26), TEXT, anchor="lm")

    # panels
    for (px1, py1, px2, py2, title, kind, content) in spec["panels"]:
        panel(img, px1, py1, px2, py2)
        d = ImageDraw.Draw(img)
        tracked(d, (px1 + 18, py1 + 14), title, font(F_SEMI, 9), MUTED, 1.2)
        if kind == "text":
            y = py1 + 44
            for col, line in content:
                d.ellipse(s(px1 + 20, y + 5, px1 + 27, y + 12), fill=col)
                for ln in wrap(line, font(F_REG, 11.5), px2 - px1 - 60):
                    text(d, (px1 + 38, y), ln, font(F_REG, 11.5), TEXT)
                    y += 18
                y += 10
        elif kind == "table":
            cols = [px1 + 20, px2 - 170, px2 - 80]
            y = py1 + 42
            for r, row in enumerate(content):
                f = font(F_SEMI, 9.5) if r == 0 else font(F_SEMI if r == 1 else F_REG, 11.5)
                c = MUTED if r == 0 else (TEAL if r == 1 else TEXT)
                for cx, val in zip(cols, row):
                    text(d, (cx, y), val.upper() if r == 0 else val, f, c)
                y += 26 if r == 0 else 24
                if r == 0:
                    d.line(s(px1 + 18, y - 6, px2 - 18, y - 6), fill=PANEL_BORDER, width=S)

    # draw at 2x for crisp anti-aliasing, then save at exactly 1280x720 so Power BI shows it 1:1 on a 1280x720 page
    img.convert("RGB").resize((W, H), Image.LANCZOS).save(OUT / f"{spec['file']}.png", optimize=True)
    print("saved", spec["file"])


if __name__ == "__main__":
    for spec in LAYOUT:
        render(spec)
