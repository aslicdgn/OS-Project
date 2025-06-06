# themes.py
# Açık ve koyu tema için stil ayarları
def get_light_theme():
    return {
        "bg": "#f9f9f9",
        "fg": "#222",
        "status_bg": "#e9e9e9",
        "status_fg": "#222",
        "accent": "#1976d2"
    }

def get_dark_theme():
    return {
        "bg": "#23272e",
        "fg": "#fafafa",
        "status_bg": "#2c313a",
        "status_fg": "#fafafa",
        "accent": "#90caf9"
    }
