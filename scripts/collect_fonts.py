"""Fetch open-license Latin font subsets once; builds use the bundled files."""
import re
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/"web"/"public"/"fonts"
target.mkdir(parents=True,exist_ok=True)
url="https://fonts.googleapis.com/css2?family=Inter:wght@400..800&family=Manrope:wght@400..800&display=swap"
request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"})
css=urllib.request.urlopen(request,timeout=30).read().decode()
for family in ("Inter","Manrope"):
    blocks=re.findall(r"@font-face\s*\{([^}]+)\}",css)
    block=next(b for b in blocks if f"'{family}'" in b and "U+0000-00FF" in b)
    font_url=re.search(r"url\(([^)]+)\)",block).group(1)
    data=urllib.request.urlopen(font_url,timeout=30).read()
    (target/f"{family.lower()}-latin.woff2").write_bytes(data)
    license_url=f"https://raw.githubusercontent.com/google/fonts/main/ofl/{family.lower()}/OFL.txt"
    (target/f"{family}-OFL.txt").write_bytes(urllib.request.urlopen(license_url,timeout=30).read())
    print(f"{family}: {len(data)} bytes, OFL license bundled.")

