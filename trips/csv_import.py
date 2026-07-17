"""Pure CSV parsing helper for the CSV import feature.

No database access — keeps this easy to unit-test in isolation.
"""
import csv
import io

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
MAX_ROWS = 500
NAME_MAX_LENGTH = 120


def parse_items_csv(file):
    """Parse an uploaded CSV file and return (rows, skipped, error).

    ``file`` is a Django InMemoryUploadedFile / TemporaryUploadedFile (i.e. any
    file-like object with a ``.read()`` method and a ``.size`` attribute, or a
    raw ``bytes`` / ``str`` object for tests).

    Returns:
        rows    – list of dicts {name, quantity, category_name}
        skipped – number of data rows skipped due to blank name
        error   – a human-readable error string, or None on success

    Parsing stops early (returns error) when:
    - file size exceeds MAX_FILE_SIZE
    - data row count exceeds MAX_ROWS
    - file cannot be decoded as UTF-8
    - 'name' column is absent
    """
    # --- size check -----------------------------------------------------------
    size = getattr(file, 'size', None)
    if size is None:
        # Fall back for raw bytes / str objects in tests.
        raw = file if isinstance(file, (bytes, str)) else None
        if raw is not None:
            size = len(raw.encode('utf-8') if isinstance(raw, str) else raw)
    if size is not None and size > MAX_FILE_SIZE:
        return [], 0, f'File is too large (max {MAX_FILE_SIZE // 1024 // 1024} MB).'

    # --- read bytes -----------------------------------------------------------
    try:
        raw_bytes = file.read() if hasattr(file, 'read') else (
            file.encode('utf-8') if isinstance(file, str) else file
        )
    except Exception as exc:
        return [], 0, f'Could not read file: {exc}'

    if len(raw_bytes) > MAX_FILE_SIZE:
        return [], 0, f'File is too large (max {MAX_FILE_SIZE // 1024 // 1024} MB).'

    # --- decode ---------------------------------------------------------------
    try:
        text = raw_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        return [], 0, 'File could not be decoded as UTF-8. Please save your CSV as UTF-8.'

    # --- parse CSV ------------------------------------------------------------
    reader = csv.DictReader(io.StringIO(text))

    try:
        fieldnames = reader.fieldnames
    except Exception as exc:
        return [], 0, f'Could not parse CSV: {exc}'

    if not fieldnames:
        return [], 0, "CSV has no header row or is empty."

    # Map lowercased fieldname → actual fieldname
    lower_map = {f.strip().lower(): f for f in fieldnames}

    if 'name' not in lower_map:
        return [], 0, "CSV is missing a required 'name' column."

    name_col = lower_map['name']
    qty_col = lower_map.get('quantity')
    cat_col = lower_map.get('category')

    rows = []
    skipped = 0
    data_row_count = 0

    try:
        for raw_row in reader:
            data_row_count += 1
            if data_row_count > MAX_ROWS:
                return [], 0, f'File has more than {MAX_ROWS} data rows.'

            name = (raw_row.get(name_col) or '').strip()
            if not name:
                skipped += 1
                continue

            # Truncate to model max length
            name = name[:NAME_MAX_LENGTH]

            # Quantity: blank / non-numeric / < 1 → 1
            quantity = 1
            if qty_col:
                qty_raw = (raw_row.get(qty_col) or '').strip()
                if qty_raw:
                    try:
                        parsed = int(qty_raw)
                        if parsed >= 1:
                            quantity = parsed
                    except (ValueError, TypeError):
                        pass  # default to 1

            # Category: blank → None
            category_name = None
            if cat_col:
                cat_raw = (raw_row.get(cat_col) or '').strip()
                if cat_raw:
                    category_name = cat_raw

            rows.append({'name': name, 'quantity': quantity, 'category_name': category_name})

    except csv.Error as exc:
        return [], 0, f'Could not parse CSV: {exc}'

    return rows, skipped, None
