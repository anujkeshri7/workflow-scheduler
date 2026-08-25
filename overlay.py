import json
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

DATA_FILE = "daily_news_data.json"

FONT_IMPACT    = r"C:\Windows\Fonts\impact.ttf"
FONT_ARIAL_BD  = r"C:\Windows\Fonts\arialbd.ttf"
FONT_ARIAL     = r"C:\Windows\Fonts\arial.ttf"

def gf(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def fit_crop(img, target_w, target_h):
    """Crop-fit image to exact dimensions preserving centre."""
    iw, ih = img.size
    tr = target_w / target_h
    cr = iw / ih
    if cr > tr:
        new_w = int(ih * tr)
        left  = (iw - new_w) // 2
        img   = img.crop((left, 0, left + new_w, ih))
    else:
        new_h = int(iw / tr)
        img   = img.crop((0, 0, iw, new_h))
    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


# ──────────────────────────────────────────────────────────────────────────────
# TEMPLATE 1 : GRID CONTROVERSY
# Dark bottom panel · yellow headline · red category pill
# Best for : controversy / political drama / film gossip
# ──────────────────────────────────────────────────────────────────────────────
def render_grid_controversy(img_raw, item, out_path):
    W, H = 1080, 1350
    PHOTO_H = 660          # photo occupies top 660 px
    PANEL_H = H - PHOTO_H  # text panel = 690 px

    # ── canvas ──────────────────────────────────────────────────────────────
    canvas = Image.new("RGB", (W, H), (12, 12, 12))

    # ── photo section ───────────────────────────────────────────────────────
    img = fit_crop(img_raw.convert("RGB"), W, PHOTO_H)

    # simulate 3-panel grid with black dividers (reference style)
    dw = ImageDraw.Draw(img)
    mid_x   = W // 2
    mid_y_r = PHOTO_H // 2          # divider on right half only
    # vertical centre divider
    dw.rectangle([mid_x-3, 0, mid_x+3, PHOTO_H], fill=(0,0,0))
    # horizontal divider on right side (top-right / bottom-right split)
    dw.rectangle([mid_x, mid_y_r-3, W, mid_y_r+3], fill=(0,0,0))

    canvas.paste(img, (0, 0))

    # thin red top strip
    dw2 = ImageDraw.Draw(canvas)
    dw2.rectangle([0, 0, W, 6], fill=(220, 20, 60))

    # ── watermark ───────────────────────────────────────────────────────────
    dw2.text((40, 14), "@news.report.in",
             font=gf(FONT_ARIAL, 26), fill=(255, 255, 255))

    # ── text panel ──────────────────────────────────────────────────────────
    PY = PHOTO_H + 18   # panel top-padding

    # category pill
    cat_map = {
        "controversy": "CONTROVERSY",
        "breaking":    "BREAKING NEWS",
        "politics":    "POLITICS",
        "film":        "BOLLYWOOD",
        "sports":      "SPORTS",
    }
    cat_txt = item.get("category", cat_map.get(item.get("template","breaking"), "NEWS")).upper()
    f_cat = gf(FONT_IMPACT, 36)
    pill_w = int(len(cat_txt) * 19.5)
    dw2.rectangle([40, PY, 40 + pill_w, PY + 50], fill=(220, 20, 60))
    dw2.text((55, PY + 7), cat_txt, font=f_cat, fill=(255, 255, 255))
    PY += 62

    # headline  – YELLOW, large
    headline  = item.get("headline", "").upper()
    f_head    = gf(FONT_IMPACT, 72)
    max_chars = 22
    # auto-shrink font until all lines fit in width
    for sz in range(72, 38, -2):
        f_head = gf(FONT_IMPACT, sz)
        ok = all(dw2.textlength(l, font=f_head) <= (W - 80)
                 for l in headline.split("\n"))
        if ok:
            break
    dw2.multiline_text((40, PY), headline, font=f_head,
                       fill=(255, 215, 0), spacing=6)
    try:
        hb = dw2.multiline_textbbox((40, PY), headline, font=f_head, spacing=6)
        PY = hb[3] + 18
    except Exception:
        PY += 160

    # subheadline – white
    sub      = item.get("subheadline", "")
    f_sub    = gf(FONT_ARIAL_BD, 33)
    w_sub    = textwrap.fill(sub, width=42)
    dw2.multiline_text((40, PY), w_sub, font=f_sub,
                       fill=(230, 230, 230), spacing=5)
    try:
        sb = dw2.multiline_textbbox((40, PY), w_sub, font=f_sub, spacing=5)
        PY = sb[3] + 18
    except Exception:
        PY += 140

    # fact box – yellow bg / black text
    fact = item.get("highlighted_fact", "")
    if fact and PY + 52 < H - 20:
        f_fact = gf(FONT_ARIAL_BD, 32)
        fw = min(int(len(fact) * 19), W - 80)
        dw2.rectangle([40, PY, 40 + fw, PY + 50], fill=(255, 215, 0))
        dw2.text((55, PY + 9), fact, font=f_fact, fill=(10, 10, 10))

    canvas.save(out_path)
    print(f"[grid_controversy] OK -> {out_path}")


# ──────────────────────────────────────────────────────────────────────────────
# TEMPLATE 2 : SPLIT POLITICS
# Navy blue bottom panel · white headline · gold accent bar
# Best for : diplomacy / governance / positive national news
# ──────────────────────────────────────────────────────────────────────────────
def render_split_politics(img_raw, item, out_path):
    W, H    = 1080, 1350
    PHOTO_H = 690
    NAVY    = (8, 20, 58)

    canvas = Image.new("RGB", (W, H), NAVY)
    img    = fit_crop(img_raw.convert("RGB"), W, PHOTO_H)

    # subtle vignette on bottom edge of photo
    vig = Image.new("RGBA", (W, PHOTO_H), (0,0,0,0))
    vd  = ImageDraw.Draw(vig)
    for y in range(PHOTO_H - 120, PHOTO_H):
        a = int(200 * (y - (PHOTO_H - 120)) / 120)
        vd.line([(0,y),(W,y)], fill=(0,0,0,a))
    img = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")

    canvas.paste(img, (0, 0))
    dw = ImageDraw.Draw(canvas)

    # blue separator line
    dw.rectangle([0, PHOTO_H, W, PHOTO_H + 5], fill=(30, 120, 255))

    # watermark
    dw.text((40, 18), "@news.report.in",
            font=gf(FONT_ARIAL, 26), fill=(255,255,255))

    PY = PHOTO_H + 22

    # category pill
    cat_map = {
        "politics":    "POLITICS",
        "controversy": "CONTROVERSY",
        "breaking":    "BREAKING NEWS",
        "film":        "BOLLYWOOD",
        "sports":      "SPORTS",
    }
    cat_txt = item.get("category", cat_map.get(item.get("template","politics"), "NEWS")).upper()
    f_cat   = gf(FONT_IMPACT, 35)
    pill_w  = int(len(cat_txt) * 19)
    dw.rectangle([40, PY, 40 + pill_w, PY + 48], fill=(30, 120, 255))
    dw.text((54, PY + 6), cat_txt, font=f_cat, fill=(255,255,255))
    PY += 60

    # headline – white, bold
    headline = item.get("headline","").upper()
    f_head   = gf(FONT_IMPACT, 68)
    for sz in range(68, 36, -2):
        f_head = gf(FONT_IMPACT, sz)
        ok = all(dw.textlength(l, font=f_head) <= (W - 80)
                 for l in headline.split("\n"))
        if ok:
            break
    dw.multiline_text((40, PY), headline, font=f_head,
                      fill=(255,255,255), spacing=6)
    try:
        hb = dw.multiline_textbbox((40, PY), headline, font=f_head, spacing=6)
        PY = hb[3] + 14
    except Exception:
        PY += 155

    # gold accent underline
    dw.rectangle([40, PY, 220, PY + 4], fill=(255, 200, 0))
    PY += 20

    # subheadline – soft blue-white
    sub   = item.get("subheadline","")
    f_sub = gf(FONT_ARIAL, 32)
    w_sub = textwrap.fill(sub, width=44)
    dw.multiline_text((40, PY), w_sub, font=f_sub,
                      fill=(195, 210, 255), spacing=5)
    try:
        sb = dw.multiline_textbbox((40, PY), w_sub, font=f_sub, spacing=5)
        PY = sb[3] + 18
    except Exception:
        PY += 135

    # fact box – gold bg / dark text
    fact = item.get("highlighted_fact","")
    if fact and PY + 50 < H - 20:
        f_fact = gf(FONT_ARIAL_BD, 32)
        fw = min(int(len(fact)*19), W-80)
        dw.rectangle([40, PY, 40+fw, PY+48], fill=(255,200,0))
        dw.text((55, PY+8), fact, font=f_fact, fill=(10,10,10))

    canvas.save(out_path)
    print(f"[split_politics] OK -> {out_path}")


# ──────────────────────────────────────────────────────────────────────────────
# TEMPLATE 3 : IMPACT BREAKING
# Full-bleed image · heavy dark gradient · red/white large text on image
# Best for : urgent breaking / legal crisis / court drama
# ──────────────────────────────────────────────────────────────────────────────
def render_impact_breaking(img_raw, item, out_path):
    W, H = 1080, 1350

    img = fit_crop(img_raw.convert("RGBA"), W, H)

    # deep gradient from 40% down
    grad = Image.new("RGBA", (W, H), (0,0,0,0))
    gd   = ImageDraw.Draw(grad)
    fade_start = int(H * 0.35)
    for y in range(fade_start, H):
        a = min(255, int(255 * (y - fade_start) / (H * 0.40)))
        gd.line([(0,y),(W,y)], fill=(0,0,0,a))

    composite = Image.alpha_composite(img, grad)
    dw = ImageDraw.Draw(composite)

    # red top strip
    dw.rectangle([0, 0, W, 7], fill=(220, 20, 60, 255))

    # watermark
    dw.text((40, 18), "@news.report.in",
            font=gf(FONT_ARIAL,26), fill=(255,255,255,200))

    # category pill
    cat_map = {
        "breaking": "BREAKING NEWS",
        "sports":   "SPORTS",
        "politics": "POLITICS",
        "film":     "BOLLYWOOD"
    }
    cat_txt = item.get("category", cat_map.get(item.get("template","breaking"), "BREAKING NEWS")).upper()
    f_cat = gf(FONT_IMPACT, 40)
    pill_w = int(len(cat_txt) * 20)
    dw.rectangle([40, 820, 40 + pill_w, 875], fill=(220,20,60,255))
    dw.text((56, 828), cat_txt, font=f_cat, fill=(255,255,255,255))

    # headline — line 1 RED, rest WHITE
    headline = item.get("headline","").upper()
    lines    = headline.split("\n")
    f_head   = gf(FONT_IMPACT, 80)
    for sz in range(80, 40, -2):
        f_head = gf(FONT_IMPACT, sz)
        ok = all(dw.textlength(l, font=f_head) <= (W - 80) for l in lines)
        if ok:
            break

    hy = 890
    for i, line in enumerate(lines):
        col = (255, 55, 55, 255) if i == 0 else (255, 255, 255, 255)
        dw.text((40, hy), line, font=f_head, fill=col)
        try:
            bb = dw.textbbox((40, hy), line, font=f_head)
            hy = bb[3] + 8
        except Exception:
            hy += int(f_head.size * 1.15)

    hy += 10

    # subheadline – light grey
    sub   = item.get("subheadline","")
    f_sub = gf(FONT_ARIAL, 34)
    w_sub = textwrap.fill(sub, width=42)
    dw.multiline_text((40, hy), w_sub, font=f_sub,
                      fill=(210,210,210,255), spacing=6)
    try:
        sb = dw.multiline_textbbox((40, hy), w_sub, font=f_sub, spacing=6)
        hy = sb[3] + 16
    except Exception:
        hy += 140

    # fact box – red bg / white text
    fact = item.get("highlighted_fact","")
    if fact and hy + 50 < H - 20:
        f_fact = gf(FONT_ARIAL_BD, 32)
        fw = min(int(len(fact)*19), W-80)
        dw.rectangle([40, hy, 40+fw, hy+48], fill=(220,20,60,255))
        dw.text((55, hy+8), fact, font=f_fact, fill=(255,255,255,255))

    composite.convert("RGB").save(out_path)
    print(f"[impact_breaking] OK -> {out_path}")


# ──────────────────────────────────────────────────────────────────────────────
# DISPATCH TABLE  — maps template name → renderer function
# ──────────────────────────────────────────────────────────────────────────────
DISPATCH = {
    "controversy": render_grid_controversy,
    "breaking":    render_impact_breaking,
    "politics":    render_split_politics,
    "film":        render_grid_controversy,
    "sports":      render_impact_breaking,
}


def draw_news_posts():
    if not os.path.exists(DATA_FILE):
        print(f"[Error] {DATA_FILE} not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("posts", []):
        img_path = item.get("image_path","")
        out_path = item.get("out_path","")

        if not os.path.exists(img_path):
            print(f"[Warning] Skipping — image not found: {img_path}")
            continue

        img_raw  = Image.open(img_path)
        # Sanitize headline to ensure fonts without rupee glyph render properly
        if "headline" in item:
            item["headline"] = item["headline"].replace("₹", "RS. ")
        t_type   = item.get("template","breaking")
        renderer = DISPATCH.get(t_type, render_impact_breaking)

        try:
            renderer(img_raw, item, out_path)
        except Exception as e:
            import traceback
            print(f"[Failed] [{t_type}]: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    draw_news_posts()
