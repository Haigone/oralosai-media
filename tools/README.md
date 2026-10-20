# Strumenti ORA LO SAI
- tools/ols.py: renderer delle slide (PIL + font Anton), ricerca foto libere su Wikimedia Commons.
  API: search(query, n, minh) -> [{url, lic, author, title}], photo(url) -> immagine 1080x1350,
  cover(img, testo, tag, acc), inner(img, testo, n, totale, kicker, big, acc), follow(img), to_bytes(img).
  Nel testo *parole* = colore accento.
