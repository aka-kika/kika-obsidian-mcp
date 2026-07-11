# Bases examples

Copyable examples for the Bases tools (`create_base`, `update_base`, `get_base`, `list_bases`, `delete_base`).

A [Base](https://help.obsidian.md/bases) is a `.base` file: plain YAML describing database-like views over your notes. This server validates every base against the [official schema](https://help.obsidian.md/bases/syntax) before writing, so an invalid base is rejected with a message naming the offending path (for example, `views[0].sort[0] missing 'property' key`) rather than silently producing a file Obsidian won't open.

The tool arguments mirror the schema:

- `views` (required) — a list of view objects. Each has a `type` (`table`, `list`, `cards`, or `map`) and usually a `name` and an `order`.
- `filters` (optional) — a global filter: either a single string statement, or a mapping with one of `and` / `or` / `not` holding a list of conditions.
- `formulas` (optional) — a mapping of formula name to expression string.
- `properties` (optional) — a mapping of property name to config such as `displayName`.
- `summaries` (optional) — a mapping of summary name to expression string.

---

## 1. Task tracker

Tracks notes tagged `#task`, splits active vs. completed into two table views, groups active tasks by status, and computes a "days until due" column.

Call `create_base` with `path = "Bases/Tasks.base"` and:

```json
{
  "filters": { "and": ["file.hasTag(\"task\")", "file.ext == \"md\""] },
  "formulas": {
    "days_until_due": "if(due, (date(due) - today()).days, \"\")",
    "priority_label": "if(priority == 1, \"🔴 High\", if(priority == 2, \"🟡 Medium\", \"🟢 Low\"))"
  },
  "properties": {
    "status": { "displayName": "Status" },
    "formula.days_until_due": { "displayName": "Days Until Due" }
  },
  "views": [
    {
      "type": "table",
      "name": "Active Tasks",
      "filters": { "and": ["status != \"done\""] },
      "order": ["file.name", "status", "formula.priority_label", "due", "formula.days_until_due"],
      "groupBy": { "property": "status", "direction": "ASC" },
      "summaries": { "formula.days_until_due": "Average" }
    },
    {
      "type": "table",
      "name": "Completed",
      "filters": { "and": ["status == \"done\""] },
      "order": ["file.name", "completed_date"]
    }
  ]
}
```

Which produces:

```yaml
filters:
  and:
  - file.hasTag("task")
  - file.ext == "md"
formulas:
  days_until_due: if(due, (date(due) - today()).days, "")
  priority_label: if(priority == 1, "🔴 High", if(priority == 2, "🟡 Medium", "🟢 Low"))
properties:
  status:
    displayName: Status
  formula.days_until_due:
    displayName: Days Until Due
views:
- type: table
  name: Active Tasks
  filters:
    and:
    - status != "done"
  order:
  - file.name
  - status
  - formula.priority_label
  - due
  - formula.days_until_due
  groupBy:
    property: status
    direction: ASC
  summaries:
    formula.days_until_due: Average
- type: table
  name: Completed
  filters:
    and:
    - status == "done"
  order:
  - file.name
  - completed_date
```

---

## 2. Project index

Indexes every note in a `Projects/` folder as both a card gallery and a sortable table, with a computed "days since last touched" value.

Call `create_base` with `path = "Bases/Projects.base"` and:

```json
{
  "filters": "file.inFolder(\"Projects\")",
  "formulas": {
    "days_idle": "(now() - file.mtime).days",
    "status_icon": "if(status == \"active\", \"🟢\", if(status == \"paused\", \"🟡\", \"⚪️\"))"
  },
  "properties": {
    "formula.days_idle": { "displayName": "Idle (days)" },
    "formula.status_icon": { "displayName": "" }
  },
  "views": [
    {
      "type": "cards",
      "name": "Gallery",
      "order": ["cover", "file.name", "status", "formula.status_icon"]
    },
    {
      "type": "table",
      "name": "All Projects",
      "order": ["file.name", "status", "formula.days_idle", "file.mtime"],
      "sort": [{ "property": "file.mtime", "direction": "DESC" }],
      "limit": 50
    }
  ]
}
```

Note the single-string global filter (`file.inFolder(...)`), the `sort` list on the table view, and `limit`.

---

## 3. Daily notes overview

A `list` view over dated daily notes, most recent first.

Call `create_base` with `path = "Bases/Daily.base"` and:

```json
{
  "filters": {
    "and": [
      "file.inFolder(\"Daily Notes\")",
      "/^\\d{4}-\\d{2}-\\d{2}$/.matches(file.basename)"
    ]
  },
  "formulas": {
    "day_of_week": "date(file.basename).format(\"dddd\")"
  },
  "properties": {
    "formula.day_of_week": { "displayName": "Day" }
  },
  "views": [
    {
      "type": "list",
      "name": "Recent Days",
      "order": ["file.name", "formula.day_of_week"],
      "sort": [{ "property": "file.name", "direction": "DESC" }],
      "limit": 30
    }
  ]
}
```

---

## 4. Places map

A `map` view that pins notes by a `coordinates` property, colouring and
labelling each marker from other properties. The `map` layout is provided by the
[Maps community plugin](https://obsidian.md/plugins?id=maps) — its per-view keys
(`coordinates`, `markerIcon`, `markerColor`, `defaultZoom`, …) round-trip
unchanged, so a base Obsidian saved with a map view can be re-read and re-written
without tripping validation.

Call `create_base` with `path = "Bases/Places.base"` and:

```json
{
  "filters": "file.hasTag(\"place\")",
  "views": [
    {
      "type": "map",
      "name": "Map",
      "order": ["file.name", "rating"],
      "coordinates": "note.coordinates",
      "markerIcon": "note.icon",
      "markerColor": "note.color",
      "defaultZoom": 12
    },
    {
      "type": "table",
      "name": "All Places",
      "order": ["file.name", "rating"],
      "sort": [{ "property": "rating", "direction": "DESC" }]
    }
  ]
}
```

Which produces:

```yaml
filters: file.hasTag("place")
views:
- type: map
  name: Map
  order:
  - file.name
  - rating
  coordinates: note.coordinates
  markerIcon: note.icon
  markerColor: note.color
  defaultZoom: 12
- type: table
  name: All Places
  order:
  - file.name
  - rating
  sort:
  - property: rating
    direction: DESC
```

---

## Updating a base

`update_base` merges into the existing file — it does not overwrite the whole thing.

- **Replace one view, leave the rest alone** — match by `name`:

  ```json
  { "upsert_views": [{ "type": "cards", "name": "Gallery", "order": ["cover", "file.name"] }] }
  ```

- **Add a new view** — an `upsert_views` entry whose `name` doesn't exist yet is appended.

- **Remove views** by name:

  ```json
  { "remove_views": ["Completed"] }
  ```

- **Add or change a formula** (a `null` value deletes that formula):

  ```json
  { "formulas": { "days_idle": "(now() - file.mtime).days", "old_formula": null } }
  ```

- **Replace the global filter** — pass `filters`; to drop it entirely, pass `replace_filters: true` and leave `filters` unset.

Each update is re-validated as a whole and (when `OBSIDIAN_BACKUP_ON_WRITE=true`) the original is copied into `.obsidian-mcp-backups/` first.

---

## Reading and listing

- `get_base(path)` returns `{ path, data, raw, views, parse_error }`. If the file has broken YAML, `data` is `null`, `parse_error` holds the message, and `raw` still gives you the original text.
- `list_bases(folder?)` returns each `.base` with its `path` and `views` (the view names), so you can discover bases without reading each one.
