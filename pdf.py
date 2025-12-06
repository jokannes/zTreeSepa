import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def MakePDF(file_path, experiment_name, payments, currency, reference):
    doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph(f"<b>Experiment: {experiment_name}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Table data: header + rows
    data = [["Index", "Name", "IBAN", "Amount", "Currency", "Reference"]]
    total_sum = 0

    for idx, payment in enumerate(payments, 1):
        data.append([
            str(idx),
            payment["name"],
            payment["iban"],
            f"{payment['amount']:.2f}",
            currency,
            reference
        ])
        total_sum += payment['amount']

    # Table style
    table = Table(data, repeatRows=1, hAlign='LEFT')
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ])
    table.setStyle(table_style)

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Total sum
    total_amount = sum(p["amount"] for p in payments)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Gesamtsumme:</b> {total_amount:.2f} {currency}", styles['Normal']))
    
    # Signature line
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Unterschrift Experimentator: ____________________________", styles['Normal']))
    
    # Timestamp
    timestamp = datetime.datetime.now().strftime("Datei erstellt am %d.%m.%Y um %H:%M Uhr")
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<i>{timestamp}</i>", styles['Normal']))

    # Build PDF
    doc.build(elements)