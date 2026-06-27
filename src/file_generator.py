from docx import Document
from markdown_pdf import MarkdownPdf, Section


def generate_pdf(title: str, content: str, filepath: str) -> bool:
    try:
        pdf = MarkdownPdf(toc_level=2)
        full_content = f"# {title}\n\n{content}"
        pdf.add_section(Section(full_content))
        pdf.save(filepath)
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False


def generate_word(title: str, content: str, filepath: str) -> bool:
    try:
        doc = Document()
        doc.add_heading(title, level=1)

        # Add content, handling line breaks
        for paragraph in content.split("\n"):
            if paragraph.strip():
                doc.add_paragraph(paragraph.strip())

        doc.save(filepath)
        return True
    except Exception as e:
        print(f"Error generating Word document: {e}")
        return False
