import tkinter as tk
from tkinter import filedialog

def get_file():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    return filedialog.askopenfilename(
        title="Select a TXT File",
        filetypes=[("Text Files", "*.txt")],
    )
