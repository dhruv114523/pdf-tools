# PDF Tools

A pair of simple desktop utilities for working with PDFs. Files are processed
locally on your computer; they are not uploaded to a website or a third-party
service.

## What it does

### PDF page reorderer

Run `pdf_reorder.py` to rearrange pages in an existing PDF. Preview pages and
select one or more pages to move up, down, to the beginning, or to the end. You
can also reverse the entire page order or reset it. Save the reordered PDF as a
new file; pages are rearranged without rasterizing them, preserving their
original content and quality. Password-protected PDFs are not supported.

### PDF & image merger

Run `merge.py` to open the merger. Add PDFs and images, arrange their order,
preview pages, and rotate individual pages before saving everything as one
PDF. Supported image formats are PNG, JPG/JPEG, WebP, BMP, TIF, and TIFF.

### PDF compressor

Run `pdf_compressor.py` to open the compressor. Choose a PDF, preview its pages,
and set a maximum output size in KB or MB. The app tries progressively smaller
rendering settings and saves a result only when it gets below the requested
size. Compression rasterizes each page into an image, so text may no longer be
selectable or searchable, and visual quality can be reduced. Password-protected
PDFs are not supported.

## Requirements

- Python 3
- Tkinter (included with many Python installations; on some Linux distributions
  it must be installed separately)
- PyMuPDF
- Pillow
- pypdf

Install the Python packages:

```bash
python -m pip install PyMuPDF Pillow pypdf
```

## Run

Start either tool from a terminal in this directory:

```bash
python pdf_reorder.py
```

```bash
python merge.py
```

```bash
python pdf_compressor.py
```

## About

This project is 100% AI-generated, made for me and for anyone else who might
find it useful. I wanted a straightforward way to handle PDFs without having
to upload personal documents to a sketchy website.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
