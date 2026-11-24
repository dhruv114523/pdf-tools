import os
import tkinter as tk

from tkinter import filedialog, messagebox

import fitz
from PIL import Image, ImageTk


# =============================================
# PAGE ORDER HELPERS
# =============================================
#
# These work on a plain list called "order", where
# order[position] is the ORIGINAL (0-based) page number
# that currently sits at that position.
#
# Each helper changes the list in place and returns the
# new positions of the selected rows, so the UI can keep
# them highlighted after the move.


def shift_up(order, selected):

    taken = set()
    new_selected = []

    for index in sorted(selected):

        if index > 0 and (index - 1) not in taken:

            order[index - 1], order[index] = (
                order[index],
                order[index - 1]
            )

            index -= 1

        taken.add(index)
        new_selected.append(index)

    return sorted(new_selected)


def shift_down(order, selected):

    last = len(order) - 1

    taken = set()
    new_selected = []

    for index in sorted(selected, reverse=True):

        if index < last and (index + 1) not in taken:

            order[index], order[index + 1] = (
                order[index + 1],
                order[index]
            )

            index += 1

        taken.add(index)
        new_selected.append(index)

    return sorted(new_selected)


def send_to_top(order, selected):

    chosen_set = set(selected)

    chosen = [order[i] for i in sorted(selected)]

    rest = [
        page for i, page in enumerate(order)
        if i not in chosen_set
    ]

    order[:] = chosen + rest

    return list(range(len(chosen)))


def send_to_bottom(order, selected):

    chosen_set = set(selected)

    chosen = [order[i] for i in sorted(selected)]

    rest = [
        page for i, page in enumerate(order)
        if i not in chosen_set
    ]

    order[:] = rest + chosen

    return list(range(len(rest), len(order)))


# =============================================
# APPLICATION
# =============================================


class PDFReorderer:

    PREVIEW_WIDTH = 430
    PREVIEW_HEIGHT = 450

    def __init__(self, root):

        self.root = root
        self.root.title("PDF Page Reorderer")
        self.root.geometry("1050x750")
        self.root.minsize(850, 620)

        self.input_file = None
        self.total_pages = 0
        self.page_order = []
        self.preview_image = None
        self.edit_buttons = []

        self.create_ui()

    # =========================================
    # UI
    # =========================================

    def create_ui(self):

        # Header
        header = tk.Frame(self.root)
        header.pack(fill="x", pady=(15, 10))

        tk.Label(
            header,
            text="PDF Page Reorderer",
            font=("Arial", 20, "bold")
        ).pack()

        tk.Label(
            header,
            text="Rearrange the pages of an existing PDF.",
            font=("Arial", 10)
        ).pack(pady=5)

        # -------------------------------------
        # BOTTOM CONTROLS
        # (packed before the main area so they
        # are never pushed off a small window)
        # -------------------------------------

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=10
        )

        self.save_button = tk.Button(
            bottom_frame,
            text="SAVE REORDERED PDF",
            font=("Arial", 12, "bold"),
            bg="#287A45",
            fg="white",
            width=25,
            height=2,
            command=self.save_pdf,
            state="disabled"
        )

        self.save_button.pack(pady=5)

        self.status = tk.Label(
            bottom_frame,
            text="Waiting for a PDF.",
            font=("Arial", 9),
            fg="gray"
        )

        self.status.pack(pady=5)

        # Main area
        main_frame = tk.Frame(self.root)
        main_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )

        # -------------------------------------
        # LEFT: FILE INFO + PAGE ORDER
        # -------------------------------------

        left_frame = tk.LabelFrame(
            main_frame,
            text="Page Order",
            font=("Arial", 11, "bold"),
            padx=15,
            pady=10
        )

        left_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )

        tk.Button(
            left_frame,
            text="Select PDF",
            width=20,
            command=self.select_pdf
        ).pack(pady=(5, 5))

        self.filename_label = tk.Label(
            left_frame,
            text="No PDF selected",
            font=("Arial", 10),
            wraplength=380
        )

        self.filename_label.pack(pady=3)

        info_frame = tk.Frame(left_frame)
        info_frame.pack(pady=3)

        self.original_size_label = tk.Label(
            info_frame,
            text="Size: -",
            font=("Arial", 10)
        )

        self.original_size_label.pack(
            side="left",
            padx=10
        )

        self.page_count_label = tk.Label(
            info_frame,
            text="Pages: -",
            font=("Arial", 10)
        )

        self.page_count_label.pack(
            side="left",
            padx=10
        )

        tk.Label(
            left_frame,
            text=(
                "Click a page to select it. Use Ctrl/Shift-click "
                "to select several. Pages in a new position are "
                "shown in blue."
            ),
            font=("Arial", 9),
            fg="gray",
            wraplength=380
        ).pack(pady=(5, 5))

        # Page list
        list_frame = tk.Frame(left_frame)
        list_frame.pack(
            fill="both",
            expand=True,
            pady=5
        )

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.page_listbox = tk.Listbox(
            list_frame,
            font=("Arial", 11),
            selectmode="extended",
            exportselection=False,
            activestyle="none",
            yscrollcommand=scrollbar.set
        )

        self.page_listbox.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.config(
            command=self.page_listbox.yview
        )

        self.page_listbox.bind(
            "<<ListboxSelect>>",
            lambda event: self.show_preview()
        )

        # Reorder buttons
        button_frame = tk.Frame(left_frame)
        button_frame.pack(pady=(5, 0))

        buttons = [
            ("Move Up", self.move_up),
            ("Move Down", self.move_down),
            ("Move to Top", self.move_to_top),
            ("Move to Bottom", self.move_to_bottom),
            ("Reverse All", self.reverse_pages),
            ("Reset Order", self.reset_order)
        ]

        for index, (text, command) in enumerate(buttons):

            button = tk.Button(
                button_frame,
                text=text,
                width=13,
                command=command,
                state="disabled"
            )

            button.grid(
                row=index // 3,
                column=index % 3,
                padx=4,
                pady=4
            )

            self.edit_buttons.append(button)

        # -------------------------------------
        # RIGHT: PREVIEW
        # -------------------------------------

        right_frame = tk.LabelFrame(
            main_frame,
            text="Page Preview",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )

        right_frame.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.preview_label = tk.Label(
            right_frame,
            text="Select a PDF to preview",
            bg="#eeeeee",
            fg="gray",
            font=("Arial", 12)
        )

        self.preview_label.pack(
            fill="both",
            expand=True,
            pady=5
        )

        self.preview_caption = tk.Label(
            right_frame,
            text="",
            font=("Arial", 10)
        )

        self.preview_caption.pack(pady=10)

    # =========================================
    # SELECT PDF
    # =========================================

    def select_pdf(self):

        file = filedialog.askopenfilename(
            title="Select PDF",
            filetypes=[
                ("PDF files", "*.pdf")
            ]
        )

        if not file:
            return

        try:

            document = fitz.open(file)

            if document.is_encrypted:

                document.close()

                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

            if len(document) == 0:

                document.close()

                raise ValueError(
                    "This PDF contains no pages."
                )

            total_pages = len(document)

            document.close()

            size = os.path.getsize(file)

            self.input_file = file
            self.total_pages = total_pages
            self.page_order = list(range(total_pages))

            self.filename_label.config(
                text=os.path.basename(file)
            )

            self.original_size_label.config(
                text=f"Size: {self.format_size(size)}"
            )

            self.page_count_label.config(
                text=f"Pages: {self.total_pages}"
            )

            for button in self.edit_buttons:

                button.config(
                    state="normal"
                )

            self.refresh_list(selected=[0])

            self.status.config(
                text="PDF loaded successfully."
            )

        except Exception as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

    # =========================================
    # FORMAT FILE SIZE
    # =========================================

    def format_size(self, size):

        if size >= 1024 * 1024:

            return f"{size / (1024 * 1024):.2f} MB"

        return f"{size / 1024:.2f} KB"

    # =========================================
    # PAGE LIST
    # =========================================

    def refresh_list(self, selected=None):

        if selected is None:
            selected = []

        self.page_listbox.delete(0, "end")

        for position, original in enumerate(self.page_order):

            self.page_listbox.insert(
                "end",
                f"{position + 1:>4}.     Page {original + 1}"
            )

            # Highlight pages that are not in their original spot
            if original != position:

                self.page_listbox.itemconfig(
                    position,
                    foreground="#1a5fb4"
                )

        for index in selected:

            self.page_listbox.selection_set(index)

        if selected:

            self.page_listbox.see(selected[0])
            self.page_listbox.activate(selected[0])

        moved = sum(
            1 for position, original in enumerate(self.page_order)
            if position != original
        )

        if moved:

            self.status.config(
                text=f"{moved} page(s) in a new position."
            )

        else:

            self.status.config(
                text="Page order unchanged."
            )

        self.update_save_button()
        self.show_preview()

    def get_selected(self):

        selected = list(
            self.page_listbox.curselection()
        )

        if not selected:

            self.status.config(
                text="Select one or more pages first."
            )

        return selected

    def update_save_button(self):

        changed = (
            self.input_file is not None
            and self.page_order != list(range(self.total_pages))
        )

        self.save_button.config(
            state="normal" if changed else "disabled"
        )

    # =========================================
    # PDF PREVIEW
    # =========================================

    def show_preview(self):

        if not self.input_file or not self.page_order:
            return

        selection = self.page_listbox.curselection()

        position = selection[0] if selection else 0

        original = self.page_order[position]

        try:

            document = fitz.open(self.input_file)

            try:

                page = document.load_page(original)

                rect = page.rect

                # Scale the page to fit the preview area
                zoom = min(
                    self.PREVIEW_WIDTH / rect.width,
                    self.PREVIEW_HEIGHT / rect.height
                )

                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(zoom, zoom),
                    alpha=False
                )

                image = Image.frombytes(
                    "RGB",
                    [pixmap.width, pixmap.height],
                    pixmap.samples
                )

            finally:

                document.close()

            self.preview_image = ImageTk.PhotoImage(
                image
            )

            self.preview_label.config(
                image=self.preview_image,
                text=""
            )

            self.preview_caption.config(
                text=(
                    f"Original page {original + 1}  "
                    f"(now at position {position + 1} "
                    f"of {self.total_pages})"
                )
            )

        except Exception as error:

            messagebox.showerror(
                "Preview error",
                str(error)
            )

    # =========================================
    # REORDER ACTIONS
    # =========================================

    def move_up(self):

        selected = self.get_selected()

        if not selected:
            return

        self.refresh_list(
            shift_up(self.page_order, selected)
        )

    def move_down(self):

        selected = self.get_selected()

        if not selected:
            return

        self.refresh_list(
            shift_down(self.page_order, selected)
        )

    def move_to_top(self):

        selected = self.get_selected()

        if not selected:
            return

        self.refresh_list(
            send_to_top(self.page_order, selected)
        )

    def move_to_bottom(self):

        selected = self.get_selected()

        if not selected:
            return

        self.refresh_list(
            send_to_bottom(self.page_order, selected)
        )

    def reverse_pages(self):

        if not self.page_order:
            return

        last = len(self.page_order) - 1

        selected = [
            last - index
            for index in self.page_listbox.curselection()
        ]

        self.page_order.reverse()

        self.refresh_list(sorted(selected))

    def reset_order(self):

        if not self.page_order:
            return

        self.page_order = list(range(self.total_pages))

        self.refresh_list()

    # =========================================
    # SAVE REORDERED PDF
    # =========================================

    def save_pdf(self):

        if not self.input_file:
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Reordered PDF",
            defaultextension=".pdf",
            initialfile="reordered_document.pdf",
            filetypes=[
                ("PDF files", "*.pdf")
            ]
        )

        if not output_path:
            return

        # Prevent overwriting original PDF
        if (
            os.path.normcase(os.path.realpath(output_path))
            == os.path.normcase(os.path.realpath(self.input_file))
        ):

            messagebox.showerror(
                "Invalid output",
                "You cannot overwrite the original PDF."
            )

            return

        self.save_button.config(
            state="disabled"
        )

        self.status.config(
            text="Saving reordered PDF. Please wait..."
        )

        self.root.update_idletasks()

        temp_path = output_path + ".tmp"

        try:

            document = fitz.open(self.input_file)

            try:

                # Rearranges the pages in place. The pages are not
                # re-rendered, so text, vectors and quality are kept.
                document.select(self.page_order)

                document.save(
                    temp_path,
                    garbage=4,
                    deflate=True
                )

            finally:

                document.close()

            os.replace(
                temp_path,
                output_path
            )

            temp_path = None

            final_size = os.path.getsize(
                output_path
            )

            messagebox.showinfo(
                "Saved successfully",
                f"PDF reordered successfully!\n\n"
                f"Pages: {self.total_pages}\n"
                f"File size: {self.format_size(final_size)}\n\n"
                f"Saved to:\n{output_path}"
            )

            self.status.config(
                text=(
                    f"Saved: {os.path.basename(output_path)} "
                    f"({self.format_size(final_size)})"
                )
            )

        except Exception as error:

            messagebox.showerror(
                "Save failed",
                str(error)
            )

            self.status.config(
                text="Save failed."
            )

        finally:

            if temp_path and os.path.exists(temp_path):

                os.remove(temp_path)

            self.update_save_button()


# =============================================
# RUN APPLICATION
# =============================================

if __name__ == "__main__":

    root = tk.Tk()

    app = PDFReorderer(root)

    root.mainloop()