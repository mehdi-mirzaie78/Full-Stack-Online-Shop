# Storefront fonts

Self-hosted with `next/font/local`; no runtime Google Fonts requests.

- **Vazirmatn** variable WOFF2, weights 100–900: Persian UI and Persian fallback in English content. Source: https://github.com/rastikerdar/vazirmatn/blob/master/fonts/webfonts/Vazirmatn%5Bwght%5D.woff2
- **Manrope** Latin variable WOFF2, weights 200–800: English UI and explicitly marked Latin content. Source: https://fonts.gstatic.com/s/manrope/v23/xn7gYHE41ni1AdIRggexSg.woff2

Both use SIL Open Font License 1.1; original license notices live alongside these files. Manrope source/license: https://github.com/google/fonts/tree/main/ofl/manrope

Set `lang="fa"` or `lang="en"` for mixed-language content. CSS selects font stack from language, not text direction. Persian headings use natural letter spacing and extra line height; reserve monospace for technical identifiers, not Persian labels/prices.
