from playwright.sync_api import sync_playwright
from pathlib import Path

URL = "https://my.clevelandclinic.org/health/diseases"
NAV_TIMEOUT_MS = 60000
OUTPUT_DIR = Path("diseases")

def file_safe(s: str) -> str:
    return "0-9" if any(ch.isdigit() for ch in s) or "#" in s else s

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

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.set_default_timeout(NAV_TIMEOUT_MS)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        page.goto(URL, wait_until="domcontentloaded")
        accept_cookies_if_any(page)

        page.wait_for_selector(".az-letters__container a")
        letters = [t.strip() for t in page.locator(".az-letters__container a").all_inner_texts() if t.strip()]

        for letter in letters:
            page.locator(".az-letters__container a", has_text=letter).first.click()
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            page.wait_for_function(
                """
                (L) => {
                  const isDigit = (ch) => /[0-9]/.test(ch);
                  const cards = [...document.querySelectorAll(".results__single a[href*='/health/diseases/']")].filter(a => {
                    const cs = getComputedStyle(a);
                    return a.offsetParent !== null && cs.display !== "none" && cs.visibility !== "hidden";
                  });
                  if (cards.length === 0) return false;
                  const titleEl = cards[0].querySelector(".index-list__title");
                  if (!titleEl) return false;
                  const t = titleEl.textContent.trim();
                  if (!t) return false;
                  const ch = t[0].toUpperCase();
                  if (L.includes("0") || L.includes("9") || L.includes("#")) return /[0-9]/.test(ch);
                  return ch === L;
                }
                """,
                arg=letter,
                timeout=60000
            )

            anchors = page.locator(".results__single a[href*='/health/diseases/']:visible")
            handles = anchors.element_handles()

            pairs = []
            for h in handles:
                href = h.get_attribute("href")
                try:
                    title = h.query_selector(".index-list__title").inner_text().strip()
                except Exception:
                    title = (h.inner_text() or "").strip()
                if not href or not title:
                    continue
                title = " ".join(title.split())
                pairs.append((title, href))

            seen = set()
            uniq = []
            for t, u in pairs:
                key = (t, u)
                if key not in seen:
                    seen.add(key)
                    uniq.append((t, u))

            fname = OUTPUT_DIR / f"diseases_{file_safe(letter)}.txt"
            with open(fname, "w", encoding="utf-8") as f:
                for t, u in uniq:
                    f.write(f"{t}:{u}\n")

            print(f"{letter}: {len(uniq)} itens -> {fname}")

        browser.close()

if __name__ == "__main__":
    main()
