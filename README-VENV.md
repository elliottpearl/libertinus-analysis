# Python Development Environments

This project uses **two separate Python virtual environments**, because the system FontForge module is compiled for **Python 3.11**, while the rest of the project uses **modern Python (3.12+)** and modern versions of `fonttools`, `uharfbuzz`, and other dependencies.

Both environments install dependencies from **`pyproject.toml`**, ensuring consistent versions across the project.

---

# 1. Normal Development Environment (Python 3.12+, no FontForge)

This is the environment used for all regular development.  
It does **not** include FontForge and does **not** need Python 3.11.

VS Code should automatically activate this environment.

### Create the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

(`pip install -e .` installs dependencies from `pyproject.toml`.)

### Activate it (normal workflow)

```bash
source .venv/bin/activate
```

### Deactivate it

```bash
deactivate
```

This environment remains clean and modern.  
Use it for everything except scripts that import `fontforge`.

---

# 2. FontForge‑Dedicated Environment (Python 3.11)

This environment is only for scripts that import the system FontForge module.

FontForge on this system is compiled for:

```
libpython3.11.so.1.0
```

so the venv must use **Python 3.11**.

### Create the environment

```bash
python3.11 -m venv .venv-fontforge
source .venv-fontforge/bin/activate
pip install -e .
```

### Inject the system FontForge module

FontForge cannot be installed via pip.  
Instead, symlink the system module into the venv:

```bash
ln -s /usr/lib/python3/dist-packages/fontforge*.so \
      .venv-fontforge/lib/python3.11/site-packages/
```

### Activate it (when running fontforge scripts)

```bash
source .venv-fontforge/bin/activate
```

### Deactivate it

```bash
deactivate
```

Use this environment for:

```
./run_implied_anchors.py
```

or any script that imports `fontforge`.

---

# 3. Switching Between Environments

You can freely switch between the two environments.  
There is no need to delete or recreate them.

### Normal → FontForge

```bash
# if normal venv is active
deactivate

source .venv-fontforge/bin/activate
```

### FontForge → Normal

```bash
deactivate

source .venv/bin/activate
```
