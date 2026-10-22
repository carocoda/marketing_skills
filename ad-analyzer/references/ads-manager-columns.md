# Ads Manager export: columns and formulas

Exports differ per account, column preset, language and attribution setting. Never expect an exact set. Read the header row, map whatever is there to the fields below, and tell the person which fields you found, which you mapped by guess, and which are missing.

## Common column names (English exports)

| Field | Typical Meta Ads Manager names | Also seen |
|---|---|---|
| Ad name | `Ad name` | `Ad Name`, `Ad` |
| Ad set / campaign | `Ad set name`, `Campaign name` | |
| Delivery | `Ad delivery`, `Delivery status` | |
| Dates | `Reporting starts`, `Reporting ends` | `Day` (daily breakdown) |
| Spend | `Amount spent (EUR)`, `Amount spent (USD)` | any currency in brackets |
| Impressions | `Impressions` | |
| Reach | `Reach` | |
| Frequency | `Frequency` | |
| Results | `Results` | next to `Result indicator` / `Result type` |
| Cost per result | `Cost per result` | `Cost per results` |
| Link clicks | `Link clicks` | `Clicks (all)` is NOT the same: it includes likes and profile clicks |
| CTR | `CTR (link click-through rate)` | `CTR (all)` (not the same) |
| CPC | `CPC (cost per link click) (EUR)` | `CPC (all)` |
| CPM | `CPM (cost per 1,000 impressions) (EUR)` | |
| 3-second plays | `3-second video plays` | `Video plays` (older exports) |
| ThruPlays | `ThruPlays` | `ThruPlay actions` |
| Quartiles | `Video plays at 25%`, `Video plays at 50%`, `Video plays at 75%`, `Video plays at 95%`, `Video plays at 100%` | |
| Average watch time | `Video average play time` | |
| Landing page views | `Landing page views` | `Website landing page views` |
| Purchases / leads / registrations | `Purchases`, `Leads`, `Website registrations completed`, `Adds to cart` | `Website purchases`, conversion value columns |
| Conversion value | `Purchases conversion value` | `Website purchase ROAS (return on ad spend)` |

Non-English exports: match by meaning (for example Dutch `Besteed bedrag`, `Weergaven`, `Bereik`, `Klikken op link`; German `Ausgegebener Betrag`, `Impressionen`, `Reichweite`, `Link-Klicks`). If a mapping is not obvious, ask.

Exports from other platforms (TikTok, LinkedIn, Google) work the same way: map to these fields and skip the metrics that don't exist there.

## Reading the file

```python
import pandas as pd
df = pd.read_csv(path)            # or pd.read_excel(path) for .xlsx (needs openpyxl)
print(df.columns.tolist())        # map these first
```

Watch for:
- A **totals row** at the top or bottom (no ad name, or "Total"): drop it before ranking.
- **Numbers as text** with thousand separators or currency signs, or decimal commas in European exports: clean them before calculating.
- **Daily breakdowns** (one row per ad per day): group by ad name and sum the counts before calculating rates. Never average rates.
- **Mixed result types** across rows (one ad optimised for leads, another for purchases): compare cost per result only within the same result type.

## Formulas (show these in the report)

| Metric | Formula | Rule of thumb |
|---|---|---|
| CTR (link) | link clicks / impressions | depends on niche; compare within the account |
| CPM | spend / impressions x 1000 | high CPM points at audience or placement |
| CPC (link) | spend / link clicks | |
| Hook rate | 3-second plays / impressions | under 25% weak, over 35% strong |
| Hold rate | ThruPlays / 3-second plays | low means the middle loses people |
| Cost per result | spend / results | rank on this, within one result type |
| Frequency | impressions / reach | above ~3 on cold audiences hints at fatigue |
| Click to landing | landing page views / link clicks | low means a slow or broken page |
| Conversion rate | results / link clicks (or / landing page views) | |

Calculate from the raw counts when you can, rather than trusting the export's own rate columns: they may use a different click definition.
