
import io, json, re, os, hashlib, time, urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1350
M = 150
ACC = (255, 90, 31); WHITE = (255, 255, 255); BG = (10, 10, 10)
UA = {"User-Agent": "OraLoSaiBot/1.0 (oralosainews)"}
os.makedirs("/home/user/cache", exist_ok=True)
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
def get_cached(u):
    fn = "/home/user/cache/" + hashlib.md5(u.encode()).hexdigest()
    if os.path.exists(fn): return open(fn, "rb").read()
    for i in range(4):
        try:
            b = get(u); open(fn, "wb").write(b); return b
        except Exception:
            time.sleep(3 + 4 * i)
    raise RuntimeError("download failed " + u)
if not os.path.exists("/home/user/Anton.ttf"):
    open("/home/user/Anton.ttf", "wb").write(get("https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf"))
def font(sz): return ImageFont.truetype("/home/user/Anton.ttf", sz)

def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for i in range(5):
        try: return json.loads(get(url))
        except Exception: time.sleep(2 + 3 * i)
    return {}
OKL = ("cc0", "cc by", "cc-by", "public domain", "pd")
def search(q, n=15, minh=1000):
    d = api({"action":"query","generator":"search","gsrsearch":q + " filetype:bitmap","gsrnamespace":6,"gsrlimit":n,"prop":"imageinfo","iiprop":"url|size|extmetadata|mime","iiurlwidth":1600,"format":"json"})
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    out = []
    for p in pages:
        ii = p["imageinfo"][0]; md = ii.get("extmetadata", {}); lic = md.get("LicenseShortName", {}).get("value", ""); low = lic.lower()
        if ii.get("mime") not in ("image/jpeg", "image/png") or ii["height"] < minh or ii["width"] < 800: continue
        if not any(k in low for k in OKL) or "sa" in re.split(r"[\s-]+", low): continue
        out.append(dict(title=p["title"], url=ii.get("thumburl") or ii["url"], lic=lic, page=ii["descriptionurl"], author=re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "?"))[:60]))
    return out

def photo(url):
    im = Image.open(io.BytesIO(get_cached(url))).convert("RGB")
    r = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))

def shade(im, stops):
    mask = Image.new("L", (1, H)); vals = []
    for y in range(H):
        f = (H - y) / H; a = 0
        for (f0, a0), (f1, a1) in zip(stops, stops[1:]):
            if f0 <= f <= f1: a = a0 + (a1 - a0) * (f - f0) / (f1 - f0); break
        else:
            if f > stops[-1][0]: a = stops[-1][1]
        vals.append(int(a))
    mask.putdata(vals); mask = mask.resize((W, H))
    base = im.convert("RGB").copy(); base.paste(Image.new("RGB", (W, H), BG), (0, 0), mask); return base

def tokens(text):
    out = []
    for i, part in enumerate(re.split(r"\*", text)):
        words = part.upper().split()
        if i > 0 and words and part[:1] not in (" ", "") and out:
            m = re.match(r"^[^\w]+", words[0])
            if m:
                lw, la = out[-1]; out[-1] = (lw + m.group(0), la); words[0] = words[0][len(m.group(0)):]
        for w in words:
            if w: out.append((w, i % 2 == 1))
    merged = []
    for w, a in out:
        if merged and merged[-1][0][-1:] in ("'", "’"): merged[-1] = (merged[-1][0] + w, a)
        else: merged.append((w, a))
    return merged

def wrap(tok, f, maxw):
    lines, cur = [], []
    for w, a in tok:
        t = " ".join([x for x, _ in cur] + [w])
        if f.getlength(t) <= maxw or not cur: cur.append((w, a))
        else: lines.append(cur); cur = [(w, a)]
    if cur: lines.append(cur)
    return lines

def draw_rich(d, x, ybottom, text, sz, lh, maxw=780, acc=ACC):
    f = font(sz); lines = wrap(tokens(text), f, maxw); y = ybottom - len(lines) * lh; top = y
    for ln in lines:
        cx = x
        for w, a in ln:
            d.text((cx, y), w, font=f, fill=acc if a else WHITE); cx += f.getlength(w + " ")
        y += lh
    return top

def spaced(d, xy, text, f, fill, sp):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill); x += f.getlength(ch) + sp
    return x

def cover(img, text, tag=None, acc=ACC):
    im = shade(img, [(0, 245), (0.34, 237), (0.52, 150), (0.76, 0)]); d = ImageDraw.Draw(im)
    top = draw_rich(d, M, H - 190, text, 98, 100, acc=acc)
    d.rectangle([M, top - 40, M + 130, top - 35], fill=acc)
    spaced(d, (M, top - 100), "ORA LO SAI", font(36), acc, 6.5)
    spaced(d, (M, H - 100), "SCORRI A DESTRA  →", font(30), (210, 210, 210), 5)
    if tag:
        f = font(34); w = sum(f.getlength(c) + 5 for c in tag.upper()) + 44
        d.rectangle([M, 70, M + w, 131], fill=acc); spaced(d, (M + 22, 76), tag.upper(), f, BG, 5)
    return im

def inner(img, text, n, total, kicker=None, big=None, acc=ACC):
    im = shade(img, [(0, 247), (0.40, 217), (0.80, 64), (1.0, 64)]); d = ImageDraw.Draw(im)
    top = draw_rich(d, M, H - 190, text, 78, 86, acc=acc)
    if kicker: spaced(d, (M, top - 70), kicker.upper(), font(44), acc, 3.5); top -= 70
    if big: d.text((M, top - 220), big, font=font(200), fill=acc)
    f = font(30); t = f"{n}/{total}"
    d.text((W - M - f.getlength(t), H - 100), t, font=f, fill=(160, 160, 160))
    return im

def follow(bgimg, handle="@oralosainews", acc=ACC):
    im = Image.alpha_composite(bgimg.convert("RGBA"), Image.new("RGBA", (W, H), BG + (209,))).convert("RGB"); d = ImageDraw.Draw(im)
    spaced(d, (M, 262), "ORA LO SAI", font(36), acc, 6.5); d.rectangle([M, 322, M + 130, 327], fill=acc)
    y = 370; f = font(118)
    for t, c in [("SE NON CI SEGUI,", WHITE), ("NON CI VEDRAI", acc), ("PIÙ.", WHITE)]:
        d.text((M, y), t, font=f, fill=c); y += 121
    d.text((M, y + 30), "Le notizie che girano, prima di tutti.", font=font(44), fill=(215, 215, 215))
    bw = f"SEGUI {handle.upper()}"; fb = font(56); w = sum(fb.getlength(c) + 3 for c in bw) + 96
    d.rectangle([M, y + 120, M + w, y + 230], fill=acc); spaced(d, (M + 48, y + 130), bw, fb, BG, 3)
    spaced(d, (M, y + 290), "SALVA · CONDIVIDI · COMMENTA", font(36), (180, 180, 180), 5)
    return im

def to_bytes(im):
    b = io.BytesIO(); im.save(b, "JPEG", quality=88, optimize=True); return b.getvalue()
