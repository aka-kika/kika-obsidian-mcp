"""Obsidian Bases (.base) support: schema validation and (de)serialization.

Obsidian Bases are ``.base`` files: plain YAML with a small, well-defined
schema (https://help.obsidian.md/bases/syntax). Obsidian silently ignores a
base whose YAML is malformed or whose shape it does not understand, so this
module validates the assembled structure *before* anything is written to disk
and returns human-readable errors that name the exact offending path.

The recognized schema tracks the official docs. Top-level keys:
``filters``, ``formulas``, ``properties``, ``summaries``, ``views``. A view
supports ``type``, ``name``, ``limit``, ``filters``, ``order``, ``groupBy``,
``sort`` and ``summaries`` (plus the layout keys Obsidian's own UI writes).
"""

import copy

import yaml

# Canonical top-level ordering used when writing a base back out.
TOP_LEVEL_ORDER = ["filters", "formulas", "properties", "summaries", "views"]
TOP_LEVEL_KEYS = set(TOP_LEVEL_ORDER)

# Documented view layouts.
VIEW_TYPES = {"table", "list", "cards", "map"}

# Keys recognized inside a view. The first block is the documented schema; the
# second block is layout/display keys that Obsidian's UI emits when it saves a
# base, kept here so round-tripping a real Obsidian base does not trip the
# unknown-key guard.
VIEW_KEYS = {
    "type",
    "name",
    "limit",
    "filters",
    "order",
    "groupBy",
    "sort",
    "summaries",
    # layout keys written by Obsidian:
    "columnSize",
    "cardSize",
    "image",
    "imageAspectRatio",
    "imageFit",
    "rowHeight",
}

FILTER_LOGIC_KEYS = {"and", "or", "not"}
SORT_DIRECTIONS = {"ASC", "DESC"}
GROUP_BY_KEYS = {"property", "direction"}


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def parse_base(raw):
    """Parse ``.base`` YAML.

    Returns a ``(data, error)`` tuple. On success ``data`` is a dict and
    ``error`` is ``None``. On failure ``data`` is ``None`` and ``error`` is a
    human-readable string. An empty file parses to an empty dict.
    """
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, str(exc)

    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "Base file must be a YAML mapping at the top level"
    return data, None


def dump_base(data):
    """Serialize a base dict to YAML, preserving key order.

    Building the structure as a Python dict and letting PyYAML emit it means
    quoting (e.g. formula expressions that contain double quotes) is handled
    correctly and automatically.
    """
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


# ---------------------------------------------------------------------------
# Assembly / merge helpers
# ---------------------------------------------------------------------------

def build_base(views, filters=None, formulas=None, properties=None, summaries=None):
    """Assemble a base dict in canonical top-level order.

    ``views`` is required (the caller is responsible for passing at least one;
    schema validation enforces it). Optional sections are only included when
    provided.
    """
    data = {}
    if filters is not None:
        data["filters"] = filters
    if formulas is not None:
        data["formulas"] = formulas
    if properties is not None:
        data["properties"] = properties
    if summaries is not None:
        data["summaries"] = summaries
    data["views"] = views
    return data


def _merge_map(existing, updates):
    """Merge ``updates`` into ``existing``; a ``None`` value deletes the key."""
    result = dict(existing) if isinstance(existing, dict) else {}
    for key, value in updates.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = value
    return result


def _reorder(data):
    """Rebuild the dict with known top-level keys first, in canonical order."""
    result = {}
    for key in TOP_LEVEL_ORDER:
        if key in data:
            result[key] = data[key]
    for key in data:
        if key not in result:
            result[key] = data[key]
    return result


def merge_base(
    existing,
    filters=None,
    formulas=None,
    properties=None,
    summaries=None,
    upsert_views=None,
    remove_views=None,
    replace_filters=False,
):
    """Apply a partial update to an existing base dict and return a new dict.

    Merge semantics:

    - ``filters``: when provided, replaces the global filters wholesale (a
      filter is a single structure, so merging is meaningless). Pass
      ``replace_filters=True`` with ``filters=None`` to remove filters.
    - ``formulas`` / ``properties`` / ``summaries``: shallow-merged into the
      existing section. A value of ``None`` for a key removes that key.
    - ``remove_views``: list of view names to drop.
    - ``upsert_views``: list of view objects; each replaces the existing view
      with the same ``name`` or is appended when no match exists.

    The original ``existing`` dict is not mutated.
    """
    data = copy.deepcopy(existing) if isinstance(existing, dict) else {}

    if filters is not None:
        data["filters"] = filters
    elif replace_filters:
        data.pop("filters", None)

    for section, updates in (
        ("formulas", formulas),
        ("properties", properties),
        ("summaries", summaries),
    ):
        if updates is not None:
            merged = _merge_map(data.get(section, {}), updates)
            if merged:
                data[section] = merged
            else:
                data.pop(section, None)

    views = list(data.get("views") or [])

    if remove_views:
        remove = set(remove_views)
        views = [
            v for v in views
            if not (isinstance(v, dict) and v.get("name") in remove)
        ]

    if upsert_views:
        for new_view in upsert_views:
            name = new_view.get("name") if isinstance(new_view, dict) else None
            replaced = False
            if name is not None:
                for idx, existing_view in enumerate(views):
                    if isinstance(existing_view, dict) and existing_view.get("name") == name:
                        views[idx] = new_view
                        replaced = True
                        break
            if not replaced:
                views.append(new_view)

    data["views"] = views
    return _reorder(data)


def view_names(data):
    """Return a display name per view (falls back to type, then index)."""
    if not isinstance(data, dict):
        return []
    views = data.get("views")
    if not isinstance(views, list):
        return []
    names = []
    for index, view in enumerate(views):
        if isinstance(view, dict):
            names.append(view.get("name") or view.get("type") or "view {}".format(index))
        else:
            names.append("view {}".format(index))
    return names


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _type_name(value):
    return type(value).__name__


def _validate_filter(value, path, errors):
    """A filter is either a string statement or a mapping with exactly one of
    ``and`` / ``or`` / ``not`` whose value is a list of nested filters."""
    if isinstance(value, str):
        if not value.strip():
            errors.append("{} is an empty filter string".format(path))
        return
    if isinstance(value, dict):
        keys = list(value.keys())
        if len(keys) != 1:
            found = ", ".join(str(k) for k in keys) or "none"
            errors.append(
                "{} must have exactly one of 'and', 'or', 'not' (found: {})".format(path, found)
            )
            return
        key = keys[0]
        if key not in FILTER_LOGIC_KEYS:
            errors.append(
                "{} has unknown filter key '{}'; use 'and', 'or', or 'not'".format(path, key)
            )
            return
        items = value[key]
        if not isinstance(items, list):
            errors.append("{}.{} must be a list of conditions".format(path, key))
            return
        if not items:
            errors.append("{}.{} must have at least one condition".format(path, key))
        for i, item in enumerate(items):
            _validate_filter(item, "{}.{}[{}]".format(path, key, i), errors)
        return
    errors.append(
        "{} must be a filter string or a mapping with 'and'/'or'/'not' (got {})".format(
            path, _type_name(value)
        )
    )


def _validate_expression_map(value, path, errors):
    """``formulas`` / ``summaries``: mapping of name to a string expression."""
    if not isinstance(value, dict):
        errors.append(
            "{} must be a mapping of name to expression string (got {})".format(
                path, _type_name(value)
            )
        )
        return
    for name, expr in value.items():
        if not isinstance(name, str) or not name.strip():
            errors.append("{} has an empty or non-string name".format(path))
        if not isinstance(expr, str):
            errors.append(
                "{}.{} must be a string expression (got {})".format(path, name, _type_name(expr))
            )


def _validate_properties(value, errors):
    if not isinstance(value, dict):
        errors.append(
            "properties must be a mapping of property name to its config (got {})".format(
                _type_name(value)
            )
        )
        return
    for name, config in value.items():
        prop_path = "properties.{}".format(name)
        if not isinstance(config, dict):
            errors.append(
                "{} must be a mapping such as {{displayName: \"...\"}} (got {})".format(
                    prop_path, _type_name(config)
                )
            )
            continue
        if "displayName" in config and not isinstance(config["displayName"], str):
            errors.append("{}.displayName must be a string".format(prop_path))


def _validate_group_by(group_by, view_path, errors):
    path = "{}.groupBy".format(view_path)
    if not isinstance(group_by, dict):
        errors.append(
            "{} must be a mapping with a 'property' (and optional 'direction')".format(path)
        )
        return
    if "property" not in group_by:
        errors.append("{} missing 'property' key".format(path))
    elif not isinstance(group_by["property"], str) or not group_by["property"].strip():
        errors.append("{}.property must be a non-empty string".format(path))
    if "direction" in group_by:
        direction = group_by["direction"]
        if not isinstance(direction, str) or direction.upper() not in SORT_DIRECTIONS:
            errors.append("{}.direction must be ASC or DESC".format(path))
    for key in group_by:
        if key not in GROUP_BY_KEYS:
            errors.append(
                "{} has unknown key '{}' (allowed: property, direction)".format(path, key)
            )


def _validate_sort(sort, view_path, errors):
    path = "{}.sort".format(view_path)
    if not isinstance(sort, list):
        errors.append("{} must be a list of {{property, direction}} objects".format(path))
        return
    for i, entry in enumerate(sort):
        entry_path = "{}[{}]".format(path, i)
        if not isinstance(entry, dict):
            errors.append(
                "{} must be a mapping with 'property' and optional 'direction'".format(entry_path)
            )
            continue
        if "property" not in entry:
            errors.append("{} missing 'property' key".format(entry_path))
        elif not isinstance(entry["property"], str) or not entry["property"].strip():
            errors.append("{}.property must be a non-empty string".format(entry_path))
        if "direction" in entry:
            direction = entry["direction"]
            if not isinstance(direction, str) or direction.upper() not in SORT_DIRECTIONS:
                errors.append("{}.direction must be ASC or DESC".format(entry_path))
        for key in entry:
            if key not in GROUP_BY_KEYS:
                errors.append(
                    "{} has unknown key '{}' (allowed: property, direction)".format(entry_path, key)
                )


def _validate_view(view, index, errors):
    view_path = "views[{}]".format(index)
    if not isinstance(view, dict):
        errors.append("{} must be a mapping (got {})".format(view_path, _type_name(view)))
        return

    for key in view:
        if key not in VIEW_KEYS:
            errors.append(
                "{} has unknown key '{}'. Recognized view keys: {}".format(
                    view_path, key, ", ".join(sorted(VIEW_KEYS))
                )
            )

    if "type" not in view:
        errors.append(
            "{} missing required 'type' (one of: {})".format(
                view_path, ", ".join(sorted(VIEW_TYPES))
            )
        )
    else:
        view_type = view["type"]
        if not isinstance(view_type, str):
            errors.append("{}.type must be a string".format(view_path))
        elif view_type not in VIEW_TYPES:
            errors.append(
                "{}.type '{}' is not a known view type ({})".format(
                    view_path, view_type, ", ".join(sorted(VIEW_TYPES))
                )
            )

    if "name" in view and not isinstance(view["name"], str):
        errors.append("{}.name must be a string".format(view_path))

    if "limit" in view:
        limit = view["limit"]
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            errors.append("{}.limit must be a non-negative integer".format(view_path))

    if "filters" in view:
        _validate_filter(view["filters"], "{}.filters".format(view_path), errors)

    if "order" in view:
        order = view["order"]
        if not isinstance(order, list):
            errors.append("{}.order must be a list of property names".format(view_path))
        else:
            for i, column in enumerate(order):
                if not isinstance(column, str) or not column.strip():
                    errors.append(
                        "{}.order[{}] must be a non-empty property name string".format(view_path, i)
                    )

    if "groupBy" in view:
        _validate_group_by(view["groupBy"], view_path, errors)

    if "sort" in view:
        _validate_sort(view["sort"], view_path, errors)

    if "summaries" in view:
        summaries = view["summaries"]
        if not isinstance(summaries, dict):
            errors.append(
                "{}.summaries must be a mapping of property to summary name".format(view_path)
            )
        else:
            for prop, summary in summaries.items():
                if not isinstance(summary, str):
                    errors.append(
                        "{}.summaries.{} must be a summary name string".format(view_path, prop)
                    )


def validate_base_schema(data):
    """Validate an assembled base structure against the Bases schema.

    Returns a list of human-readable error strings, each naming the offending
    path (e.g. ``views[0].groupBy missing 'property' key``). An empty list
    means the structure is valid.
    """
    if not isinstance(data, dict):
        return ["Base must be a YAML mapping at the top level (got {})".format(_type_name(data))]

    errors = []

    for key in data:
        if key not in TOP_LEVEL_KEYS:
            errors.append(
                "Unknown top-level key '{}'. Allowed: {}".format(
                    key, ", ".join(TOP_LEVEL_ORDER)
                )
            )

    if "filters" in data:
        _validate_filter(data["filters"], "filters", errors)
    if "formulas" in data:
        _validate_expression_map(data["formulas"], "formulas", errors)
    if "summaries" in data:
        _validate_expression_map(data["summaries"], "summaries", errors)
    if "properties" in data:
        _validate_properties(data["properties"], errors)

    if "views" not in data:
        errors.append("Missing required 'views' key: a base needs at least one view")
    else:
        views = data["views"]
        if not isinstance(views, list):
            errors.append("views must be a list of view objects (got {})".format(_type_name(views)))
        elif not views:
            errors.append("views must contain at least one view")
        else:
            for index, view in enumerate(views):
                _validate_view(view, index, errors)

    return errors
