## 🛡️-05-15 - DOM innerText vs textContent
**Vulnerability:** Use of innerText could lead to XSS or DOM rendering issues.
**Learning:** textContent is much safer than innerText because it only updates the text node without triggering layout parsing.
**Prevention:** Use textContent for plain text UI updates.

## 🛡️-05-15 - Dynamic CSS background URLs
**Vulnerability:** Injecting unescaped dynamic paths into inline CSS `url()` properties can lead to XSS.
**Learning:** URL encoding isn't enough; using `CSS.escape()` bounds the string safely in the CSS context.
**Prevention:** Wrap dynamically set CSS properties like background images in `CSS.escape()`.
