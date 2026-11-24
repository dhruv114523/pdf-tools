import os
import io
import tkinter as tk
 
from tkinter import filedialog, messagebox
from PIL import Image, ImageOps, ImageTk
from pypdf import PdfReader, PdfWriter
import fitz
 
 
class PDFMerger:
 
    PREVIEW_BG = "#eeeeee"
 
    def __init__(self, root):
 
        self.root = root
        self.root.title("PDF & Image Merger")
        self.root.geometry("1100x800")
        self.root.minsize(900, 700)
 
        self.files = []
 
        # Store rotations as:
        # {(file_path, page_number): clockwise_degrees}
        self.rotations = {}
 
        # Preview state
        self.current_file = None
        self.current_page = 0
        self.total_pages = 0
 
        # Full-size (already rotated) image of the page being previewed.
        # It is re-fitted to the preview area every time the area changes size.
        self.source_image = None
        self.preview_image = None      # keeps a reference to the PhotoImage
        self.preview_message = "Select a file to preview"
        self.preview_message_color = "gray"
        self._resize_job = None
 
        self.create_ui()
 
    # =========================================
    # UI
    # =========================================
 
    def create_ui(self):
 
        # NOTE: pack order matters. Widgets packed earlier get their space
        # first, so the header and bottom bar are packed BEFORE the main
        # area. That way the main area can never push them off-screen.
        self.build_header()
        self.build_bottom_controls()
        self.build_main_area()
 
    # -------------------------------------
    # HEADER
    # -------------------------------------
 
    def build_header(self):
 
        header = tk.Frame(self.root)
        header.pack(side="top", fill="x", pady=(15, 10))
 
        tk.Label(
            header,
            text="PDF & Image Merger",
            font=("Arial", 20, "bold")
        ).pack()
 
        tk.Label(
            header,
            text="Arrange, preview and rotate your documents before merging.",
            font=("Arial", 10)
        ).pack(pady=5)
 
    # -------------------------------------
    # BOTTOM CONTROLS
    # -------------------------------------
 
    def build_bottom_controls(self):
 
        bottom_frame = tk.Frame(self.root)
 
        bottom_frame.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=10
        )
 
        # File management
        controls = tk.Frame(bottom_frame)
        controls.pack(pady=(0, 12))
 
        buttons = [
            ("Add Files", self.add_files),
            ("Remove", self.remove_file),
            ("Move Up ↑", self.move_up),
            ("Move Down ↓", self.move_down),
            ("Clear All", self.clear_all)
        ]
 
        for index, (label, command) in enumerate(buttons):
 
            tk.Button(
                controls,
                text=label,
                width=13,
                command=command
            ).grid(
                row=0,
                column=index,
                padx=4
            )
 
        # Create PDF
        tk.Button(
            bottom_frame,
            text="CREATE PDF",
            font=("Arial", 12, "bold"),
            bg="#287A45",
            fg="white",
            width=25,
            height=2,
            command=self.merge_files
        ).pack(pady=5)
 
        # Status
        self.status = tk.Label(
            bottom_frame,
            text="No files added.",
            font=("Arial", 9),
            fg="gray"
        )
 
        self.status.pack(pady=5)
 
    # -------------------------------------
    # MAIN AREA (file list + preview)
    # -------------------------------------
 
    def build_main_area(self):
 
        main_frame = tk.Frame(self.root)
 
        main_frame.pack(
            side="top",
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )
 
        # Two equal-width columns that share the available space
        main_frame.columnconfigure(0, weight=1, uniform="panels")
        main_frame.columnconfigure(1, weight=1, uniform="panels")
        main_frame.rowconfigure(0, weight=1)
 
        # -------------------------------------
        # LEFT PANEL: FILE LIST
        # -------------------------------------
 
        left_frame = tk.LabelFrame(
            main_frame,
            text="Files & Merge Order",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
 
        left_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )
 
        self.listbox = tk.Listbox(
            left_frame,
            font=("Arial", 10),
            selectmode=tk.BROWSE,
            activestyle="dotbox",
            exportselection=False
        )
 
        self.listbox.pack(
            side="left",
            fill="both",
            expand=True
        )
 
        scrollbar = tk.Scrollbar(
            left_frame,
            orient="vertical",
            command=self.listbox.yview
        )
 
        scrollbar.pack(side="right", fill="y")
 
        self.listbox.config(
            yscrollcommand=scrollbar.set
        )
 
        self.listbox.bind(
            "<<ListboxSelect>>",
            self.on_file_select
        )
 
        # -------------------------------------
        # RIGHT PANEL: PREVIEW
        # -------------------------------------
 
        right_frame = tk.LabelFrame(
            main_frame,
            text="Preview",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
 
        right_frame.grid(
            row=0,
            column=1,
            sticky="nsew"
        )
 
        # The controls are packed from the BOTTOM up first, and the preview
        # canvas is packed last so it simply fills whatever space is left.
        # A tall (portrait) page is scaled down to fit the canvas instead of
        # pushing the controls out of view.
 
        # ---- Rotation controls (lowest) ----
 
        rotation_frame = tk.LabelFrame(
            right_frame,
            text="Rotate Current Page",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=8
        )
 
        rotation_frame.pack(
            side="bottom",
            fill="x",
            pady=(10, 0)
        )
 
        rotation_buttons = tk.Frame(rotation_frame)
        rotation_buttons.pack(fill="x")
 
        tk.Button(
            rotation_buttons,
            text="↶ Rotate Left 90°",
            width=18,
            command=lambda: self.rotate_page(-90)
        ).pack(
            side="left",
            expand=True,
            padx=5
        )
 
        tk.Button(
            rotation_buttons,
            text="Rotate Right 90° ↷",
            width=18,
            command=lambda: self.rotate_page(90)
        ).pack(
            side="left",
            expand=True,
            padx=5
        )
 
        self.rotation_label = tk.Label(
            rotation_frame,
            text="Rotation: 0°",
            font=("Arial", 9)
        )
 
        self.rotation_label.pack(pady=(6, 0))
 
        # ---- Page navigation ----
 
        navigation = tk.Frame(right_frame)
        navigation.pack(side="bottom", pady=5)
 
        self.prev_button = tk.Button(
            navigation,
            text="← Previous",
            width=12,
            command=self.previous_page,
            state="disabled"
        )
 
        self.prev_button.grid(
            row=0,
            column=0,
            padx=5
        )
 
        self.page_label = tk.Label(
            navigation,
            text="Page - / -",
            font=("Arial", 10)
        )
 
        self.page_label.grid(
            row=0,
            column=1,
            padx=10
        )
 
        self.next_button = tk.Button(
            navigation,
            text="Next →",
            width=12,
            command=self.next_page,
            state="disabled"
        )
 
        self.next_button.grid(
            row=0,
            column=2,
            padx=5
        )
 
        # ---- File name ----
 
        self.file_info = tk.Label(
            right_frame,
            text="",
            font=("Arial", 9)
        )
 
        self.file_info.pack(side="bottom", pady=5)
 
        # ---- Preview canvas (fills the remaining space) ----
 
        self.canvas = tk.Canvas(
            right_frame,
            bg=self.PREVIEW_BG,
            highlightthickness=0,
            width=300,
            height=200
        )
 
        self.canvas.pack(
            side="top",
            fill="both",
            expand=True,
            pady=5
        )
 
        self.canvas.bind("<Configure>", self.on_canvas_resize)
 
    # =========================================
    # ADD FILES
    # =========================================
 
    def add_files(self):
 
        selected_files = filedialog.askopenfilenames(
            title="Select PDFs and Images",
            filetypes=[
                (
                    "Supported files",
                    "*.pdf *.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"
                ),
                ("PDF files", "*.pdf"),
                (
                    "Image files",
                    "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"
                )
            ]
        )
 
        for file in selected_files:
 
            if file not in self.files:
                self.files.append(file)
 
        self.refresh_list()
 
        if self.files:
            self.select_file(len(self.files) - 1)
 
    # =========================================
    # REFRESH FILE LIST
    # =========================================
 
    def refresh_list(self, selected_index=None):
 
        self.listbox.delete(0, tk.END)
 
        for index, file in enumerate(self.files):
 
            filename = os.path.basename(file)
 
            self.listbox.insert(
                tk.END,
                f"{index + 1}. {filename}"
            )
 
        self.status.config(
            text=f"{len(self.files)} file(s) added."
        )
 
        if selected_index is not None and self.files:
 
            selected_index = max(
                0,
                min(selected_index, len(self.files) - 1)
            )
 
            self.select_file(selected_index)
 
        elif not self.files:
 
            self.clear_preview()
 
    def select_file(self, index):
 
        if not self.files:
            return
 
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)
 
        self.current_page = 0
 
        self.show_preview()
 
    # =========================================
    # FILE SELECTION
    # =========================================
 
    def on_file_select(self, event=None):
 
        selection = self.listbox.curselection()
 
        if not selection:
            return
 
        self.current_page = 0
 
        self.show_preview()
 
    # =========================================
    # ROTATION
    # =========================================
 
    def rotate_page(self, degrees):
 
        if not self.current_file:
            return
 
        key = (
            self.current_file,
            self.current_page
        )
 
        current_rotation = self.rotations.get(key, 0)
 
        new_rotation = (
            current_rotation + degrees
        ) % 360
 
        self.rotations[key] = new_rotation
 
        self.show_preview()
 
    def get_rotation(self, file, page):
 
        return self.rotations.get(
            (file, page),
            0
        )
 
    # =========================================
    # PREVIEW RENDERING
    # =========================================
 
    def on_canvas_resize(self, event=None):
 
        # Debounce so we don't re-render dozens of times while dragging
        # the window edge.
        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)
 
        self._resize_job = self.root.after(60, self.render_preview)
 
    def render_preview(self):
        """Fit the current page image (or message) into the canvas."""
 
        self._resize_job = None
 
        self.canvas.delete("all")
 
        width = max(self.canvas.winfo_width(), 50)
        height = max(self.canvas.winfo_height(), 50)
 
        # No image -> show the message instead
        if self.source_image is None:
 
            self.preview_image = None
 
            self.canvas.create_text(
                width // 2,
                height // 2,
                text=self.preview_message,
                fill=self.preview_message_color,
                font=("Arial", 12),
                width=max(width - 40, 50),
                justify="center"
            )
 
            return
 
        # Scale the page down so it ALWAYS fits inside the canvas,
        # whether it is portrait or landscape.
        image = self.source_image.copy()
 
        image.thumbnail(
            (max(width - 20, 20), max(height - 20, 20)),
            Image.Resampling.LANCZOS
        )
 
        self.preview_image = ImageTk.PhotoImage(image)
 
        x0 = (width - image.width) // 2
        y0 = (height - image.height) // 2
 
        # Thin border so white pages stand out from the grey background
        self.canvas.create_rectangle(
            x0 - 1,
            y0 - 1,
            x0 + image.width,
            y0 + image.height,
            outline="#bbbbbb"
        )
 
        self.canvas.create_image(
            width // 2,
            height // 2,
            image=self.preview_image,
            anchor="center"
        )
 
    def show_message(self, text, color="gray"):
 
        self.source_image = None
        self.preview_message = text
        self.preview_message_color = color
 
        self.render_preview()
 
    # =========================================
    # DISPLAY PREVIEW
    # =========================================
 
    def show_preview(self):
 
        selection = self.listbox.curselection()
 
        if not selection:
            return
 
        index = selection[0]
        file = self.files[index]
 
        self.current_file = file
 
        extension = os.path.splitext(file)[1].lower()
 
        try:
 
            # ---------------------------------
            # PDF PREVIEW
            # ---------------------------------
 
            if extension == ".pdf":
 
                document = fitz.open(file)
 
                try:
 
                    if document.is_encrypted:
 
                        raise ValueError(
                            "Password-protected PDFs are not supported."
                        )
 
                    self.total_pages = len(document)
 
                    if self.total_pages == 0:
 
                        raise ValueError(
                            "This PDF contains no pages."
                        )
 
                    self.current_page = min(
                        self.current_page,
                        self.total_pages - 1
                    )
 
                    page = document.load_page(
                        self.current_page
                    )
 
                    pixmap = page.get_pixmap(
                        matrix=fitz.Matrix(1.5, 1.5),
                        alpha=False
                    )
 
                    image = Image.frombytes(
                        "RGB",
                        [pixmap.width, pixmap.height],
                        pixmap.samples
                    )
 
                finally:
                    document.close()
 
            # ---------------------------------
            # IMAGE PREVIEW
            # ---------------------------------
 
            else:
 
                with Image.open(file) as source:
 
                    image = ImageOps.exif_transpose(
                        source
                    ).convert("RGB")
 
                self.total_pages = 1
                self.current_page = 0
 
            # ---------------------------------
            # APPLY ROTATION (same for PDFs and images)
            # ---------------------------------
 
            rotation = self.get_rotation(
                file,
                self.current_page
            )
 
            if rotation:
 
                # PIL rotates counter-clockwise, so negate for clockwise
                image = image.rotate(
                    -rotation,
                    expand=True
                )
 
            # Keep memory use sensible for huge images. The preview is
            # fitted to the canvas afterwards in render_preview().
            image.thumbnail(
                (2000, 2000),
                Image.Resampling.LANCZOS
            )
 
            self.source_image = image
 
            self.render_preview()
 
            self.file_info.config(
                text=os.path.basename(file)
            )
 
            self.page_label.config(
                text=(
                    f"Page {self.current_page + 1} "
                    f"/ {self.total_pages}"
                )
            )
 
            self.rotation_label.config(
                text=(
                    f"Rotation: "
                    f"{rotation}° clockwise"
                )
            )
 
            self.update_navigation()
 
        except Exception as error:
 
            self.clear_preview()
 
            self.show_message(
                f"Cannot preview file:\n\n{error}",
                "red"
            )
 
    # =========================================
    # CLEAR PREVIEW
    # =========================================
 
    def clear_preview(self):
 
        self.current_file = None
        self.total_pages = 0
        self.current_page = 0
 
        self.show_message("Select a file to preview", "gray")
 
        self.file_info.config(text="")
        self.page_label.config(text="Page - / -")
        self.rotation_label.config(text="Rotation: 0°")
 
        self.prev_button.config(state="disabled")
        self.next_button.config(state="disabled")
 
    # =========================================
    # PAGE NAVIGATION
    # =========================================
 
    def update_navigation(self):
 
        self.prev_button.config(
            state=(
                "normal"
                if self.current_page > 0
                else "disabled"
            )
        )
 
        self.next_button.config(
            state=(
                "normal"
                if self.current_page < self.total_pages - 1
                else "disabled"
            )
        )
 
    def previous_page(self):
 
        if self.current_page > 0:
 
            self.current_page -= 1
 
            self.show_preview()
 
    def next_page(self):
 
        if self.current_page < self.total_pages - 1:
 
            self.current_page += 1
 
            self.show_preview()
 
    # =========================================
    # REMOVE FILE
    # =========================================
 
    def remove_file(self):
 
        selection = self.listbox.curselection()
 
        if not selection:
            return
 
        index = selection[0]
 
        removed = self.files.pop(index)
 
        # Forget any rotations that belonged to the removed file
        self.rotations = {
            key: value
            for key, value in self.rotations.items()
            if key[0] != removed
        }
 
        self.refresh_list(index)
 
    # =========================================
    # MOVE UP
    # =========================================
 
    def move_up(self):
 
        selection = self.listbox.curselection()
 
        if not selection:
            return
 
        index = selection[0]
 
        if index == 0:
            return
 
        self.files[index - 1], self.files[index] = (
            self.files[index],
            self.files[index - 1]
        )
 
        self.refresh_list(index - 1)
 
    # =========================================
    # MOVE DOWN
    # =========================================
 
    def move_down(self):
 
        selection = self.listbox.curselection()
 
        if not selection:
            return
 
        index = selection[0]
 
        if index >= len(self.files) - 1:
            return
 
        self.files[index + 1], self.files[index] = (
            self.files[index],
            self.files[index + 1]
        )
 
        self.refresh_list(index + 1)
 
    # =========================================
    # CLEAR ALL
    # =========================================
 
    def clear_all(self):
 
        self.files.clear()
        self.rotations.clear()
 
        self.listbox.delete(0, tk.END)
 
        self.clear_preview()
 
        self.status.config(
            text="All files cleared."
        )
 
    # =========================================
    # IMAGE TO PDF
    # =========================================
 
    def image_to_pdf(self, image_path):
 
        with Image.open(image_path) as source:
 
            image = ImageOps.exif_transpose(
                source
            ).convert("RGB")
 
        # NOTE: the image is NOT rotated here. The user's rotation is applied
        # to the resulting PDF page in merge_files(), together with all other
        # pages. Rotating here as well would rotate images twice.
 
        pdf_buffer = io.BytesIO()
 
        image.save(
            pdf_buffer,
            format="PDF",
            resolution=150
        )
 
        pdf_buffer.seek(0)
 
        return pdf_buffer
 
    # =========================================
    # MERGE FILES
    # =========================================
 
    def merge_files(self):
 
        if not self.files:
 
            messagebox.showwarning(
                "No files",
                "Please add some files first."
            )
 
            return
 
        output_path = filedialog.asksaveasfilename(
            title="Save Combined PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="merged_document.pdf"
        )
 
        if not output_path:
            return
 
        # Prevent overwriting an input file
        output_real = os.path.normcase(
            os.path.realpath(output_path)
        )
 
        for file in self.files:
 
            input_real = os.path.normcase(
                os.path.realpath(file)
            )
 
            if input_real == output_real:
 
                messagebox.showerror(
                    "Invalid output",
                    "Output cannot overwrite an input file."
                )
 
                return
 
        writer = PdfWriter()
 
        readers = []
        image_buffers = []
 
        try:
 
            total_pages = 0
 
            for file in self.files:
 
                extension = os.path.splitext(file)[1].lower()
 
                # ---------------------------------
                # PDF INPUT
                # ---------------------------------
 
                if extension == ".pdf":
 
                    reader = PdfReader(
                        file,
                        strict=False
                    )
 
                    if reader.is_encrypted:
 
                        raise ValueError(
                            f"Password-protected PDF:\n{file}"
                        )
 
                # ---------------------------------
                # IMAGE INPUT
                # ---------------------------------
 
                else:
 
                    image_buffer = self.image_to_pdf(
                        file
                    )
 
                    image_buffers.append(
                        image_buffer
                    )
 
                    reader = PdfReader(
                        image_buffer
                    )
 
                readers.append(reader)
 
                # ---------------------------------
                # ADD PAGES WITH ROTATIONS
                # ---------------------------------
 
                for page_number, page in enumerate(reader.pages):
 
                    rotation = self.get_rotation(
                        file,
                        page_number
                    )
 
                    if rotation:
 
                        page.rotate(rotation)
 
                    writer.add_page(page)
 
                    total_pages += 1
 
            # ---------------------------------
            # WRITE OUTPUT
            # ---------------------------------
 
            with open(output_path, "wb") as output_file:
 
                writer.write(output_file)
 
            messagebox.showinfo(
                "Success",
                f"PDF created successfully!\n\n"
                f"Total pages: {total_pages}\n\n"
                f"Saved to:\n{output_path}"
            )
 
            self.status.config(
                text=(
                    f"Successfully created PDF "
                    f"({total_pages} pages)."
                )
            )
 
        except Exception as error:
 
            messagebox.showerror(
                "Merge failed",
                f"An error occurred:\n\n{error}"
            )
 
 
# =============================================
# RUN APPLICATION
# =============================================
 
if __name__ == "__main__":
 
    root = tk.Tk()
 
    app = PDFMerger(root)
 
    root.mainloop()
 