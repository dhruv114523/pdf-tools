
import os
import tempfile
import tkinter as tk

from tkinter import filedialog, messagebox
import fitz


class PDFCompressor:

    def __init__(self, root):

        self.root = root
        self.root.title("PDF Compressor")
        self.root.geometry("1050x750")
        self.root.minsize(850, 620)

        self.input_file = None
        self.current_page = 0
        self.total_pages = 0
        self.preview_image = None

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
            text="PDF Compressor",
            font=("Arial", 20, "bold")
        ).pack()

        tk.Label(
            header,
            text="Reduce PDF file size to your desired target.",
            font=("Arial", 10)
        ).pack(pady=5)

        # Main area
        main_frame = tk.Frame(self.root)
        main_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )

        # -------------------------------------
        # LEFT: FILE INFORMATION
        # -------------------------------------

        left_frame = tk.LabelFrame(
            main_frame,
            text="Selected PDF",
            font=("Arial", 11, "bold"),
            padx=15,
            pady=15
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
        ).pack(pady=10)

        self.filename_label = tk.Label(
            left_frame,
            text="No PDF selected",
            font=("Arial", 10),
            wraplength=300
        )

        self.filename_label.pack(pady=10)

        self.original_size_label = tk.Label(
            left_frame,
            text="Original size: -",
            font=("Arial", 11)
        )

        self.original_size_label.pack(pady=10)

        self.page_count_label = tk.Label(
            left_frame,
            text="Pages: -",
            font=("Arial", 11)
        )

        self.page_count_label.pack(pady=10)

        tk.Label(
            left_frame,
            text="Target file size",
            font=("Arial", 11, "bold")
        ).pack(pady=(25, 5))

        target_frame = tk.Frame(left_frame)
        target_frame.pack()

        self.target_entry = tk.Entry(
            target_frame,
            width=12,
            font=("Arial", 12),
            justify="center"
        )

        self.target_entry.insert(0, "500")
        self.target_entry.pack(side="left", padx=5)

        self.unit_var = tk.StringVar(value="KB")

        tk.OptionMenu(
            target_frame,
            self.unit_var,
            "KB",
            "MB"
        ).pack(side="left")

        tk.Label(
            left_frame,
            text="The output must be smaller than your target.",
            font=("Arial", 9),
            fg="gray",
            wraplength=280
        ).pack(pady=10)

        # -------------------------------------
        # RIGHT: PREVIEW
        # -------------------------------------

        right_frame = tk.LabelFrame(
            main_frame,
            text="PDF Preview",
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

        # Page navigation
        navigation = tk.Frame(right_frame)
        navigation.pack(pady=10)

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

        # -------------------------------------
        # BOTTOM CONTROLS
        # -------------------------------------

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=10
        )

        self.compress_button = tk.Button(
            bottom_frame,
            text="COMPRESS PDF",
            font=("Arial", 12, "bold"),
            bg="#287A45",
            fg="white",
            width=25,
            height=2,
            command=self.compress_pdf,
            state="disabled"
        )

        self.compress_button.pack(pady=5)

        self.status = tk.Label(
            bottom_frame,
            text="Waiting for a PDF.",
            font=("Arial", 9),
            fg="gray"
        )

        self.status.pack(pady=5)

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

            self.input_file = file
            self.current_page = 0
            self.total_pages = len(document)

            document.close()

            size = os.path.getsize(file)

            self.filename_label.config(
                text=os.path.basename(file)
            )

            self.original_size_label.config(
                text=f"Original size: {self.format_size(size)}"
            )

            self.page_count_label.config(
                text=f"Pages: {self.total_pages}"
            )

            self.compress_button.config(
                state="normal"
            )

            self.status.config(
                text="PDF loaded successfully."
            )

            self.show_preview()

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
    # PDF PREVIEW
    # =========================================

    def show_preview(self):

        if not self.input_file:
            return

        try:

            document = fitz.open(self.input_file)

            page = document.load_page(
                self.current_page
            )

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(1.5, 1.5),
                alpha=False
            )

            from PIL import Image, ImageTk

            image = Image.frombytes(
                "RGB",
                [pixmap.width, pixmap.height],
                pixmap.samples
            )

            document.close()

            image.thumbnail(
                (430, 450),
                Image.Resampling.LANCZOS
            )

            self.preview_image = ImageTk.PhotoImage(
                image
            )

            self.preview_label.config(
                image=self.preview_image,
                text=""
            )

            self.page_label.config(
                text=(
                    f"Page {self.current_page + 1} "
                    f"/ {self.total_pages}"
                )
            )

            self.update_navigation()

        except Exception as error:

            messagebox.showerror(
                "Preview error",
                str(error)
            )

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
    # GET TARGET SIZE
    # =========================================

    def get_target_size(self):

        try:

            value = float(
                self.target_entry.get()
            )

            if value <= 0:
                raise ValueError

            if self.unit_var.get() == "MB":

                target = value * 1024 * 1024

            else:

                target = value * 1024

            return int(target)

        except ValueError:

            raise ValueError(
                "Please enter a valid positive target size."
            )

    # =========================================
    # RASTERIZE AND COMPRESS PDF
    # =========================================

    def create_compressed_pdf(
        self,
        input_path,
        output_path,
        dpi,
        quality
    ):

        source = fitz.open(input_path)

        output = fitz.open()

        try:

            for page_number in range(len(source)):

                page = source.load_page(page_number)

                # Preserve the rendered page dimensions
                rect = page.rect

                # Render page at the selected resolution
                pixmap = page.get_pixmap(
                    dpi=dpi,
                    colorspace=fitz.csRGB,
                    alpha=False
                )

                # Encode rendered page as JPEG
                jpeg_data = pixmap.tobytes(
                    "jpeg",
                    jpg_quality=quality
                )

                # Create a new page with original dimensions
                new_page = output.new_page(
                    width=rect.width,
                    height=rect.height
                )

                new_page.insert_image(
                    new_page.rect,
                    stream=jpeg_data
                )

            # Save with PDF optimizations
            output.save(
                output_path,
                garbage=4,
                deflate=True
            )

        finally:

            output.close()
            source.close()

    # =========================================
    # COMPRESS PDF
    # =========================================

    def compress_pdf(self):

        if not self.input_file:
            return

        try:

            target_size = self.get_target_size()

        except ValueError as error:

            messagebox.showerror(
                "Invalid target",
                str(error)
            )

            return

        output_path = filedialog.asksaveasfilename(
            title="Save Compressed PDF",
            defaultextension=".pdf",
            initialfile="compressed_document.pdf",
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

        self.compress_button.config(
            state="disabled"
        )

        self.status.config(
            text="Compressing PDF. Please wait..."
        )

        self.root.update_idletasks()

        # Compression settings, strongest last.
        # Higher DPI and quality generally mean better output.
        settings = [
            (180, 85),
            (160, 80),
            (150, 75),
            (130, 70),
            (120, 65),
            (110, 60),
            (100, 55),
            (90, 50),
            (80, 45),
            (72, 40),
            (60, 30)
        ]

        best_size = None
        best_settings = None
        temp_path = None

        try:

            # Use the destination directory for temporary output
            output_directory = os.path.dirname(
                os.path.abspath(output_path)
            )

            with tempfile.TemporaryDirectory(
                dir=output_directory
            ) as temp_directory:

                best_path = os.path.join(
                    temp_directory,
                    "best_compression.pdf"
                )

                candidate_path = os.path.join(
                    temp_directory,
                    "candidate.pdf"
                )

                # ---------------------------------
                # TRY COMPRESSION SETTINGS
                # ---------------------------------

                for index, (dpi, quality) in enumerate(settings):

                    self.status.config(
                        text=(
                            f"Trying compression "
                            f"{index + 1}/{len(settings)}... "
                            f"({dpi} DPI, quality {quality})"
                        )
                    )

                    self.root.update_idletasks()

                    self.create_compressed_pdf(
                        self.input_file,
                        candidate_path,
                        dpi,
                        quality
                    )

                    candidate_size = os.path.getsize(
                        candidate_path
                    )

                    # Keep the smallest result so far
                    if (
                        best_size is None
                        or candidate_size < best_size
                    ):

                        best_size = candidate_size
                        best_settings = (dpi, quality)

                        import shutil

                        shutil.copy2(
                            candidate_path,
                            best_path
                        )

                    # Strictly below target
                    if candidate_size < target_size:

                        break

                # ---------------------------------
                # CHECK RESULT
                # ---------------------------------

                if best_size >= target_size:

                    messagebox.showwarning(
                        "Target not achieved",
                        f"Could not reduce the PDF below "
                        f"{self.format_size(target_size)}.\n\n"
                        f"Smallest result achieved: "
                        f"{self.format_size(best_size)}\n\n"
                        f"Try a larger target size."
                    )

                    return

                # Copy successful result to destination
                import shutil

                temp_path = output_path + ".tmp"

                shutil.copy2(
                    best_path,
                    temp_path
                )

            os.replace(
                temp_path,
                output_path
            )

            temp_path = None

            original_size = os.path.getsize(
                self.input_file
            )

            final_size = os.path.getsize(
                output_path
            )

            reduction = (
                (original_size - final_size)
                / original_size
            ) * 100

            dpi, quality = best_settings

            messagebox.showinfo(
                "Compression successful",
                f"PDF compressed successfully!\n\n"
                f"Original size: "
                f"{self.format_size(original_size)}\n"
                f"Final size: "
                f"{self.format_size(final_size)}\n"
                f"Target size: "
                f"{self.format_size(target_size)}\n\n"
                f"Size reduction: {reduction:.2f}%\n"
                f"Resolution: {dpi} DPI\n"
                f"JPEG quality: {quality}\n\n"
                f"Saved to:\n{output_path}"
            )

            self.status.config(
                text=(
                    f"Compressed successfully: "
                    f"{self.format_size(final_size)} "
                    f"({reduction:.2f}% reduction)"
                )
            )

        except Exception as error:

            messagebox.showerror(
                "Compression failed",
                str(error)
            )

            self.status.config(
                text="Compression failed."
            )

        finally:

            if temp_path and os.path.exists(temp_path):

                os.remove(temp_path)

            self.compress_button.config(
                state="normal"
            )


# =============================================
# RUN APPLICATION
# =============================================

if __name__ == "__main__":

    root = tk.Tk()

    app = PDFCompressor(root)

    root.mainloop()
