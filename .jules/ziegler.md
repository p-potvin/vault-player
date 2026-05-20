## 🛡️-05-18 - VaultThemes Hex injection to ANSI sequences
**Vulnerability:** Not really a vulnerability, but a pattern needed to securely and reliably parse hex strings into ANSI sequences without format injection flaws.
**Learning:** `hex_color.lstrip('#')` combined with strict 6-char length check and base-16 integer parsing natively guards against garbage strings.
**Prevention:** Use strictly typed parsing logic when constructing dynamic terminal control sequences.

## 🛡️-05-15 - DOM innerText vs textContent
**Vulnerability:** Use of innerText could lead to XSS or DOM rendering issues.
**Learning:** textContent is much safer than innerText because it only updates the text node without triggering layout parsing.
**Prevention:** Use textContent for plain text UI updates.

## 🛡️-05-15 - Dynamic CSS background URLs
**Vulnerability:** Injecting unescaped dynamic paths into inline CSS `url()` properties can lead to XSS.
**Learning:** URL encoding isn't enough; using `CSS.escape()` bounds the string safely in the CSS context.
**Prevention:** Wrap dynamically set CSS properties like background images in `CSS.escape()`.
