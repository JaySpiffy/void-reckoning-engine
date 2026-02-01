from .json_generator import JSONReportGenerator
from .markdown_generator import MarkdownReportGenerator
from .html_generator import HTMLReportGenerator
from .csv_generator import CSVReportGenerator

from .excel_generator import ExcelReportGenerator
from .pdf_generator import PDFReportGenerator

GENERATORS = {
    "json": JSONReportGenerator,
    "markdown": MarkdownReportGenerator,
    "html": HTMLReportGenerator,
    "csv": CSVReportGenerator,
    "excel": ExcelReportGenerator,
    "pdf": PDFReportGenerator
}
