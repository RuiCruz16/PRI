from pathlib import Path
import re
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_URL = "https://my.clevelandclinic.org"
INDEX_DIR = Path("diseases")
OUTPUT_ROOT = Path("diseases")
NAV_TIMEOUT_MS = 60000

LETTERS_TO_RUN = [chr(i) for i in range(ord("A"), ord("Z")+1)] + ["0-9"]

# Acceptable section headings and their variants
SECTIONS_SPEC = [
    ("Overview", ["Overview"]),
    ("What is", ["What is"]),
    ("What are", ["What are"]),
    ("Symptoms and Causes", ["Symptoms and Causes"]),
    ("Diagnosis and Tests", ["Diagnosis and Tests"]),
    ("Management and Treatment", ["Management and Treatment"]),
    ("Outlook / Prognosis", ["Outlook / Prognosis", "Outlook/Prognosis", "Prognosis"]),
    ("Prevention", ["Prevention"]),
    ("Living With", ["Living With"]),
    ("Additional Common Questions", ["Additional Common Questions", "Frequently Asked Questions", "FAQ"]),
    ("A note from Cleveland Clinic", ["A note from Cleveland Clinic"]),
]

def safe_filename(name: str, maxlen: int = 140) -> str:
    name = re.sub(r"[\\/:*?\"<>|\n\r\t]", "_", name).strip()
    name = re.sub(r"\s+", " ", name)
    return (name[:maxlen]).rstrip(" ._")

def accept_cookies_if_any(page):
    for sel in [
        "#onetrust-accept-btn-handler",
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button[aria-label*='Accept']",
    ]:
        try:
            page.locator(sel).first.click(timeout=1500)
            break
        except Exception:
            pass

def extract_sections(page, spec):
    js = """
    (spec) => {
      const norm = s => (s||"").toLowerCase().replace(/\\s+/g," ").trim();
      const wanted = spec.map(([canon, variants]) => [canon, variants.map(norm)]);
      const out = Object.create(null);

      const isNote = (n) => n && norm((n.innerText||n.textContent||"")).startsWith(norm("A note from Cleveland Clinic"));
      const isCare = (n) => n && norm((n.innerText||n.textContent||"")).startsWith(norm("Care at Cleveland Clinic"));
      const isMetadata = (n) => {
        if (!n) return false;
        const text = norm((n.innerText||n.textContent||""));
        return text.startsWith("medically reviewed") || 
               text.startsWith("last reviewed") || 
               text.includes("learn more about the health library");
      };

      const textFromNode = (node) => {
        if (!node) return "";
        const tag = node.tagName;
        if (tag === "FIGCAPTION" || tag === "ASIDE" || tag === "FIGURE") return "";

        const text = (node.innerText || node.textContent || "").trim();
        const lowerText = text.toLowerCase();
        
        if (lowerText === "advertisement" || 
            lowerText === "policy" || 
            lowerText.startsWith("cleveland clinic is a non-profit") ||
            lowerText.includes("advertising on our site")) {
          return "";
        }
        
        const className = (node.className || "").toLowerCase();
        const id = (node.id || "").toLowerCase();
        const adKeywords = ["ad", "advertisement", "promo", "sponsored", "banner", "commercial"];
        
        if (adKeywords.some(keyword => className.includes(keyword) || id.includes(keyword))) {
          return "";
        }
        
        if (["P","DIV","SECTION"].includes(tag)) {
          return (node.innerText || "").trim();
        }
        if (["UL","OL"].includes(tag)) {
          return Array.from(node.querySelectorAll(":scope > li"))
            .map(li => (li.innerText || "").trim())
            .filter(Boolean)
            .join("\\n");
        }
        return (node.innerText || "").trim();
      };

      const headings = Array.from(document.querySelectorAll("h2, h3, h4"));

      for (let i=0; i<headings.length; i++) {
        const h = headings[i];
        const t = norm(h.textContent);
        let canonical = null;
        
        for (const [canon, variants] of wanted) {
          if ((canon === "What is" || canon === "What are") && h.tagName !== "H2") {
            continue;
          }
          if (variants.some(v => t.startsWith(v))) { canonical = canon; break; }
        }
        
        if (!canonical) continue;

        let txt = "";
        let node = h.nextElementSibling;

        while (node && !/^H[234]$/.test(node.tagName)) {
          if (isCare(node) || isMetadata(node)) break;
          
          if (isNote(node)) {
            const piece = textFromNode(node);
            if (piece) txt += (txt ? "\\n\\n" : "") + piece;
            if (canonical !== "A note from Cleveland Clinic") break;
          } else {
            const piece = textFromNode(node);
            if (piece) txt += (txt ? "\\n\\n" : "") + piece;
          }
          node = node.nextElementSibling;
        }

        if (txt = txt.trim()) {
          out[canonical] = (out[canonical] ? out[canonical] + "\\n\\n" : "") + txt;
        }
      }
      return out;
    }
    """
    return page.evaluate(js, spec)

def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.set_default_timeout(NAV_TIMEOUT_MS)

        for letter in LETTERS_TO_RUN:
            index_file = INDEX_DIR / f"diseases_{letter}.txt"
            if not index_file.exists():
                print(f"[{letter}] File not found: {index_file}. Skipping.")
                continue

            out_dir = OUTPUT_ROOT / letter
            out_dir.mkdir(parents=True, exist_ok=True)

            LINE_RE = re.compile(r'^(?P<name>.+?):\s*(?P<url>(?:https?://\S+|/\S+))$')

            items = []
            with open(index_file, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line:
                        continue
                    m = LINE_RE.match(line)
                    if not m:
                        continue
                    name = m.group("name").strip()
                    url  = m.group("url").strip()
                    if url.startswith("/"):
                        url = urljoin(BASE_URL, url)
                    items.append((name, url))

            print(f"[{letter}] {len(items)} diseases processing...")

            for i, (name, url) in enumerate(items, 1):
                fname = out_dir / f"{safe_filename(name)}.txt"
                if fname.exists():
                    print(f"  [{i}/{len(items)}] (skip) {name}")
                    continue

                try:
                    page.goto(url, wait_until="domcontentloaded")
                    accept_cookies_if_any(page)

                    page.wait_for_selector("main, article, .content, .container", timeout=30000)

                    sections = extract_sections(page, SECTIONS_SPEC)

                    lines = [name, url, ""]
                    for canonical, _variants in SECTIONS_SPEC:
                        lines.append(canonical)
                        lines.append("-" * len(canonical))
                        text = sections.get(canonical, "").strip()
                        if text:
                            lines.append(text)
                        else:
                            lines.append("(Not available)")
                        lines.append("")

                    content = "\n".join(lines).rstrip() + "\n"

                    with open(fname, "w", encoding="utf-8") as f:
                        f.write(content)

                    print(f"  [{i}/{len(items)}] OK -> {fname.name}")

                except Exception as e:
                    err_path = out_dir / f"{safe_filename(name)}.__ERROR.txt"
                    with open(err_path, "w", encoding="utf-8") as ef:
                        ef.write(f"URL: {url}\nERROR: {repr(e)}\n")
                    print(f"  [{i}/{len(items)}] ERROR in {name}: {e}")

        browser.close()

if __name__ == "__main__":
    run()
