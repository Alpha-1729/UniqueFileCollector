# 🔐 uniq-vault

> Walk, deduplicate, and organize your files into a categorized vault — blazing fast with size-based pre-filtering and parallel SHA-256 hashing.

---

## ✨ How It Works

1. **Walks** the source directory recursively and collects all file paths.
2. **Groups files by size** — files with a unique byte count cannot be duplicates and skip hashing entirely.
3. **Hashes only size-collision candidates** in parallel threads using SHA-256.
4. **Moves unique files** to the destination, organized by category and extension:

```
destination/
└── Images/
    └── jpg/
        └── [_NEW/]        ← only present on incremental runs
            └── photo.jpg
```

1. **Saves `hash.pickle`** in the destination for fast incremental future runs.

---

## 🚀 Quick Start

```bash
git clone git@github.com:Alpha-1729/uniq-vault.git
cd uniq-vault
pip install -r requirements.txt
python main.py
```

Two GUI dialogs will open — select your **source** and **destination** directories. Optionally supply a `hash.pickle` from a previous run to enable incremental mode.

---

## ⚡ Optimization: Size-Based Pre-Filtering

Hashing is the most expensive step. uniq-vault skips it entirely for files that cannot possibly be duplicates:

| Files | Action |
| --- | --- |
| **Unique size** — no other file shares the same byte count | Added directly — **no hash computed** |
| **Shared size** — one or more files have the same size | Hashed in parallel to confirm uniqueness |

In a typical photo/video library where most files differ in size, this reduces hashing work by **70–90%**.

---

## 📂 Project Structure

```
uniq-vault/
├── main.py                          # Entry point with GUI directory pickers
├── requirements.txt
│
├── config/
│   └── extension_category.json     # Extension → category mapping
│
├── core/
│   ├── **init**.py
│   ├── config.py                   # App-wide constants
│   └── collector.py                # UniqueFileCollector orchestrator
│
├── enums/
│   ├── **init**.py
│   └── hash_algorithm.py           # HashAlgorithm enum (xxhash / SHA-256 / MD5)
│
└── utils/
    ├── **init**.py
    ├── file_manager.py             # File I/O, directory dialogs, move logic
    ├── hash_calculator.py          # Pluggable file hashing
    ├── json_reader.py              # JSON config loader
    └── string_generator.py         # Random suffix generator for name collisions
```

---

## ⚙️ Configuration

### Extension Categories — `config/extension_category.json`

Maps file extensions to destination category folder names. Unknown extensions fall back to `Other/`. Add or remove entries freely.

### App Constants — `core/config.py`

| Constant | Default | Purpose |
| --- | --- | --- |
| `OTHER_FILES_DIR` | `Other` | Fallback folder for unrecognized extensions |
| `NO_EXTENSION_FILES_DIR` | `NoExt` | Folder for files with no extension |
| `HASH_FILE_NAME` | `hash.pickle` | Filename for the persisted hash set |
| `NEW_FILE_DIR_NAME` | `_NEW` | Sub-folder used in incremental runs |

### Worker Count — `main.py`

```python
collector = UniqueFileCollector(
    ...
    max_workers=4,   # Increase on machines with fast SSDs or many cores
)
```

By default, worker count is auto-detected based on CPU count.

---

## 🔁 Incremental Runs

If you've run uniq-vault before, you can supply the `hash.pickle` from the previous destination when prompted:

```
Does a previous hash file exist? (yes/no): yes
```

Files already seen in prior runs are skipped. Any new unique files are placed in a `_NEW/` sub-folder so they're easy to spot.

---

## 📦 Requirements

```
tqdm
xxhash
python-magic-bin
```

```bash
pip install -r requirements.txt
```

---

## 📄 License

MIT
