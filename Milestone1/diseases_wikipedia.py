import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

# You can find all diseases names in: https://en.wikipedia.org/wiki/Category:Lists_of_diseases

LETTERS = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
BASE = "https://en.wikipedia.org/wiki/List_of_diseases_({letter})"

HEADERS = {
    "User-Agent": "DiseaseLinkExtractor/1.0 (+mailto:ruipscruz2004@gmail.com)"
}

def extract_disease_keys_from_letter(letter: str) -> list[tuple[str, str]]:
    url = BASE.format(letter=letter)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.select_one("div.mw-parser-output")
    if content is None:
        raise RuntimeError(f"[{letter}] Couldnt find the content (.mw-parser-output).")

    pairs = []
    for a in content.select("li > a[href^='/wiki/']"):
        href = a.get("href", "")
        part = href.split("/wiki/")[1]

        if ":" in part or "#" in part:
            continue

        if "List_of_diseases_" in part:
            continue

        key = part
        human = unquote(key).replace("_", " ")
        pairs.append((key, human))

    seen = set()
    unique = []
    for k, h in pairs:
        if k not in seen:
            seen.add(k)
            unique.append((k, h))
    return unique

def main():
    total_all = 0
    for letter in LETTERS:
        try:
            items = extract_disease_keys_from_letter(letter)
            total_all += len(items)

            fname = f"diseases_{letter}.txt"
            with open(fname, "w", encoding="utf-8") as f:
                for key, _ in items:
                    f.write(key + "\n")

            print(f"[{letter}] {len(items)} itens -> {fname}")

        except Exception as e:
            print(f"[{letter}] ERRO: {e}")

        time.sleep(1)

    print(f"Total (A–Z): {total_all}")

if __name__ == "__main__":
    main()
