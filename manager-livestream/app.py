import tkinter as tk

from features.livestream.ui.main_window import LiveShopeeManagerUI


def main():
    """Start livestream UI application."""
    root = tk.Tk()
    LiveShopeeManagerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
