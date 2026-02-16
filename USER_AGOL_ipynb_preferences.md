# USER AGOL Notebook Preferences

This file captures your preferred ArcGIS Online (AGOL) notebook style and reusable boilerplate cells.

## Notebook style preference

- Keep Markdown cells for context, links, charts, and visual notes.
- Keep most operational explanations inside code cells using concise `# comments`.
- Use clear `Cell X` headers in code cells so the run order is obvious.

## Recommended cell order and templates

### Cell 0 (Markdown): Canonical AGOL starter text

```markdown
Run this cell to connect to your GIS and get started:
```

### Cell 1: Canonical AGOL connection (must be first code cell)

```python
# Cell 1: Mandatory ArcGIS connection (must be first code cell in AGOL notebooks)
# =================================================================================
from arcgis.gis import GIS
gis = GIS("home")
me = gis.users.me #Optional line

print(f"Connected to: {gis.properties.get('name', gis.properties.get('portalHostname', 'ArcGIS'))}")
print(f"User: {me.username} | Role: {me.role}")
```

### Cell 2: Install and import libraries with fallbacks

```python
# Cell 2: Install and import libraries (safe for AGOL runtime resets)
# =================================================================================
import importlib.util
import subprocess
import sys

def ensure_packages(packages):
    missing = [pkg for pkg in packages if importlib.util.find_spec(pkg) is None]
    if missing:
        print(f"Installing missing packages: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *missing])

# Add/remove packages based on notebook needs
ensure_packages(["pandas", "requests", "plotly"])

import json
import logging
import requests
import pandas as pd
import arcgis

# Import display for rich DataFrame output in notebooks
try:
    from IPython.display import display
except ImportError:
    display = print  # Fallback to standard print if IPython is not available

print("Cell 2 complete.")
```

### Cell 3: Show Python and library versions

```python
# Cell 3: Environment versions
# =================================================================================
from platform import python_version

def module_version(module_obj):
    return getattr(module_obj, "__version__", "built-in")

print("Python version:", python_version())
for p in [pd, arcgis, logging, requests, json]:
    print(f"{p.__name__:-<30}v{module_version(p)}")
```

### Cell 4: Pandas display preferences ("Excel mode")

```python
# Cell 4: Pandas display options
# =================================================================================
# import warnings
# warnings.simplefilter(action="ignore", category=FutureWarning)
pd.set_option("mode.chained_assignment", None)
pd.set_option("display.max_rows", 30)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

print("Cell 4 complete.")
```

### Cell 5: User thumbnail business card

```python
# Cell 5: AGOL user thumbnail card
# =================================================================================
from IPython.display import HTML, display, Image
import base64

me = gis.users.me

# 1) Get thumbnail link (works for modern and older ArcGIS API versions)
try:
    thumb_link = me.get_thumbnail_link()
except AttributeError:
    thumb_bytes = me.get_thumbnail()
    thumb_link = "data:image/png;base64," + base64.b64encode(thumb_bytes).decode()

# 2) Render mini business card
card_html = f"""
<div style='display:flex;align-items:center;font-family:Arial;padding:8px;
            border:1px solid #ddd;border-radius:6px;max-width:420px;'>
  <img src="{thumb_link}" style="width:80px;height:80px;border-radius:50%;margin-right:12px;">
  <div>
    <strong style="font-size:1.1em;">{me.fullName}</strong><br>
    <code>@{me.username}</code><br>
    <span>{me.role}</span><br>
    <span style="color:#666;">{gis.properties.get('name', '')}</span>
  </div>
</div>
"""
display(HTML(card_html))
```

### Cell 6: Quick list of your feature layers

```python
# Cell 6: Quick inventory of owned Feature Layers
# =================================================================================
[(it.title, it.itemid, len(it.layers))
 for it in gis.content.search(query=f"owner:{me.username}", item_type="Feature Layer")]
```

### Cell 7: Detailed table of your feature layers

```python
# Cell 7: Detailed Feature Layer inventory (owned by current user)
# =================================================================================
fl_items = gis.content.search(
    query=f"owner:{me.username}",
    item_type="Feature Layer",
    sort_field="title",
    max_items=1000
)

rows = []
for it in fl_items:
    layer_count = len(it.layers)
    rows.append({
        "Title": it.title,
        "ITEM_ID": it.itemid,
        "Layer_Count": layer_count,
        "Index_Range": f"0-{layer_count-1}" if layer_count else "-"
    })

df = pd.DataFrame(rows).sort_values("Title")
display(df)
```

### Cell 8: Print sublayer names and URLs

```python
# Cell 8: Layer detail printout (name + URL for each sublayer)
# =================================================================================
rows = []
for it in fl_items:
    for lyr in it.layers:
        print(f"  -> {lyr.properties.name}  |  {lyr.url}")
```

### Cell 9: Organization-wide feature layer inventory (English version)

```python
# Cell 9: Organization-wide Feature Layer inventory
# =================================================================================
fl_items = gis.content.search(
    query="*",
    item_type="Feature Layer",
    max_items=1000
)

rows = []
for it in fl_items:
    n = len(it.layers)
    rows.append({
        "Title": it.title,
        "ITEM_ID": it.itemid,
        "Layer_Count": n,
        "Index_Range": f"0-{n-1}" if n else "-"
    })

df = pd.DataFrame(rows).sort_values("Title")
display(df)
```

### Cell 10: Debug template (AGOL only, keep commented unless needed)

```python
# Cell 10: For debugging inside AGOL only (keep commented unless actively debugging)
# =================================================================================
# FEATURE_LAYER_ITEM_ID = "{feature_layer_item_id_for_debugging_only}"
# LAYER_INDEX = {layer_index_for_debugging_only}
# DATA_SOURCES_FILE = "/arcgis/home/{subdirectory_for_debugging_only}/{filename_for_debugging_only}"
# SOURCE_NAME = "{source_name_for_debugging_only}"
# PAGE_LIMIT = {page_limit_for_debugging_only}
# print("Cell 10: Debug configuration placeholders are ready.")
```

### Cell 11: Optional fail-fast ArcGIS connection check (production-friendly)

```python
# Cell 11: Optional ArcGIS connection check with explicit error handling
# =================================================================================
import sys
import logging
from arcgis.gis import GIS

try:
    logging.info("Connecting to ArcGIS environment...")
    gis = GIS("home")
    logging.info(f"Connected to {gis.properties.portalHostname} as {gis.users.me.username}.")
except Exception as e:
    logging.error(f"FATAL: Failed to connect to ArcGIS. Error: {e}")
    sys.exit(1)

print("Cell 11: ArcGIS connection established.")
```

### Cell 12: End-of-run confirmation with date/time

```python
# Cell 12: Final confirmation and timestamp
# =================================================================================
from datetime import datetime, timezone

utc_now = datetime.now(timezone.utc)
local_now = datetime.now().astimezone()

print("Notebook run completed successfully.")
print(f"UTC completion time:   {utc_now:%Y-%m-%d %H:%M:%S %Z}")
print(f"Local completion time: {local_now:%Y-%m-%d %H:%M:%S %Z}")

# Optional: if 'layer' exists in your workflow, show final feature count
if "layer" in globals():
    try:
        print(f"Target layer feature count: {layer.query(return_count_only=True)}")
    except Exception as e:
        print(f"Layer count check skipped: {e}")
```

## Notes

- Every AGOL notebook should start with Cell 0 (Markdown prompt) and Cell 1 (`GIS("home")`) before other logic.
- Cell 10 is intentionally commented and reserved for temporary AGOL debugging only.
- Keep Cell 11 for production diagnostics when you want explicit fail-fast behavior.
- For deterministic updates, always set and use `FEATURE_LAYER_ITEM_ID`.
- Keep this file as your template source and copy only needed cells into each notebook.
- Keep AGOL notebooks separated from notebooks meant to run outside AGOL. AGOL workflows often require AGOL-specific orchestration, authentication context (`GIS("home")`), and runtime environment handling that should not be mixed with local-only execution patterns.
- Prefer algorithmic/API catalog pulls over deterministic hardcoded lists when possible (for example, resolve current station IDs from official APIs each run).
- Add catalog safety guards before building from API pulls: request timeout, payload-size threshold (bytes), row-count threshold, and a pull timestamp for auditability.
- If catalog APIs support paging, use paging with explicit limits; if not, enforce local thresholds and fail fast with a clear message.
- Fallback order preference: official API catalog -> deterministic override/intersection with live catalog -> manual hardcoded list as last resort.
- Avoid web scraping for operational datasets when official APIs exist; scraping should be a lower-priority fallback only.
