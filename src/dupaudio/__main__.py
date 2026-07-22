"""Application entry point."""

from __future__ import annotations

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication

    # Absolute imports so this works both via `python -m dupaudio` and when
    # frozen by PyInstaller (where this file is the top-level script with no
    # package context, making relative imports fail).
    from dupaudio import APP_NAME
    from dupaudio.ui.icon import app_icon
    from dupaudio.ui.main_window import MainWindow
    from dupaudio.ui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(app_icon())
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
