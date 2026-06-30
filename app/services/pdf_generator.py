import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PDFGenerator:
    @staticmethod
    def generate(
        invoice_number: str,
        customer_name: str,
        customer_phone: str,
        total_amount: float,
        cart_items: list,
        loyalty_points: int = 0
    ) -> bytes:
        """
        Generates a professional receipt PDF using ReportLab.
        Returns the PDF content as bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=colors.HexColor('#2E8B57'), # SeaGreen theme
            spaceAfter=12,
            alignment=0
        )
        
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=10,
            spaceAfter=6
        )

        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#475569'),
            spaceAfter=4
        )

        table_header_style = ParagraphStyle(
            'TableHeaderStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.white
        )

        table_cell_style = ParagraphStyle(
            'TableCellStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#0F172A')
        )

        story = []

        # Header Title
        story.append(Paragraph("SMART RETAIL INVOICE", title_style))
        story.append(Spacer(1, 10))

        # Invoice info and Customer info in a two-column top section
        invoice_date = datetime.now().strftime("%d-%b-%Y %I:%M %p")
        meta_data = [
            [
                Paragraph(f"<b>Invoice No:</b> {invoice_number}", normal_style),
                Paragraph(f"<b>Customer Name:</b> {customer_name}", normal_style)
            ],
            [
                Paragraph(f"<b>Date/Time:</b> {invoice_date}", normal_style),
                Paragraph(f"<b>WhatsApp Number:</b> {customer_phone}", normal_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(meta_table)
        story.append(Spacer(1, 15))

        # Items Table
        story.append(Paragraph("PURCHASED PRODUCTS", section_heading))
        
        headers = [
            Paragraph("Barcode", table_header_style),
            Paragraph("Product", table_header_style),
            Paragraph("Qty", table_header_style),
            Paragraph("Price", table_header_style),
            Paragraph("GST", table_header_style),
            Paragraph("Discount", table_header_style),
            Paragraph("Subtotal", table_header_style)
        ]
        
        table_data = [headers]
        total_qty = 0

        for item in cart_items:
            total_qty += item["quantity"]
            sub = float(item["subtotal"])
            price = float(item["unit_price"])
            
            table_data.append([
                Paragraph(item["barcode"], table_cell_style),
                Paragraph(item["product_name"], table_cell_style),
                Paragraph(str(item["quantity"]), table_cell_style),
                Paragraph(f"Rs.{price:.2f}", table_cell_style),
                Paragraph("0%", table_cell_style),
                Paragraph("Rs.0.00", table_cell_style),
                Paragraph(f"Rs.{sub:.2f}", table_cell_style)
            ])

        # Grid table styles
        col_widths = [100, 150, 40, 70, 40, 60, 80]
        items_table = Table(table_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E8B57')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 15))

        # Summary Block
        summary_data = [
            [Paragraph("<b>Total Items Quantity:</b>", normal_style), Paragraph(str(total_qty), normal_style)],
            [Paragraph("<b>Loyalty Points Earned:</b>", normal_style), Paragraph(f"+{loyalty_points} Points", normal_style)],
            [Paragraph("<font color='#2E8B57'><b>Grand Total:</b></font>", section_heading), Paragraph(f"<font color='#2E8B57'><b>Rs.{total_amount:.2f}</b></font>", section_heading)]
        ]
        summary_table = Table(summary_data, colWidths=[200, 340])
        summary_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))

        # Footer
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            textColor=colors.HexColor('#94A3B8'),
            alignment=1
        )
        story.append(Paragraph("Thank you for shopping at Smart Retail store!", footer_style))

        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
