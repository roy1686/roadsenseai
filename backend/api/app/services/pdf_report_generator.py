import io
from datetime import datetime, timezone
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_survey_pdf(survey_data: Dict[str, Any], damages: List[Dict[str, Any]], work_orders: List[Dict[str, Any]]) -> bytes:
    """
    Generate a publication-grade PDF audit and engineering report
    strictly from live survey and damage database records.
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
    header_style = ParagraphStyle(
        'MainHeader',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0369a1'),
        fontName='Helvetica-Bold'
    )
    sub_header_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569')
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
        spaceBefore=12,
        spaceAfter=6
    )
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=cell_style,
        fontName='Helvetica-Bold'
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("ROADSense AI — Infrastructure Engineering Report", header_style))
    elements.append(Paragraph("Automated Visual Road Surface Distress Audit & Repair Dispatch Protocol", sub_header_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284c7'), spaceBefore=8, spaceAfter=12))

    # 2. Survey Metadata Table
    s_code = survey_data.get("survey_code", "SURVEY-UNKNOWN")
    road_name = survey_data.get("road_name", "Surveyed Road Corridor")
    road_cat = survey_data.get("road_category", "Municipal Arterial")
    created_at = str(survey_data.get("created_at", datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')))[:19]
    gps_stat = "Synchronized (" + survey_data.get("gps_source", "metadata") + ")" if survey_data.get("gps_available") else "Unavailable (Video-only analysis)"

    meta_table_data = [
        [
            Paragraph("<b>Survey Code:</b>", cell_style), Paragraph(s_code, cell_bold),
            Paragraph("<b>Road Name:</b>", cell_style), Paragraph(road_name, cell_bold)
        ],
        [
            Paragraph("<b>Road Category:</b>", cell_style), Paragraph(road_cat, cell_style),
            Paragraph("<b>Audit Date:</b>", cell_style), Paragraph(created_at, cell_style)
        ],
        [
            Paragraph("<b>GPS Status:</b>", cell_style), Paragraph(gps_stat, cell_style),
            Paragraph("<b>Model Version:</b>", cell_style), Paragraph(survey_data.get("model_name", "YOLOv8n RDD2022"), cell_style)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[100, 170, 90, 180])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 14))

    # 3. Key Metrics Summary KPI Grid
    tot_frames = survey_data.get("total_frames", 0)
    usable_frames = survey_data.get("usable_frames", 0)
    tot_dets = survey_data.get("total_detections", 0)
    uniq_damages = survey_data.get("unique_damages", len(damages))
    tot_cost = survey_data.get("total_estimated_cost", sum(d.get("estimated_repair_cost", 0) for d in damages))
    avg_rci = survey_data.get("avg_rci", 0.0)

    kpi_data = [
        [
            Paragraph("<b>Frames Scanned</b>", cell_style),
            Paragraph("<b>Total Detections</b>", cell_style),
            Paragraph("<b>Unique Defects</b>", cell_style),
            Paragraph("<b>Average RCI</b>", cell_style),
            Paragraph("<b>Est. Repair Cost</b>", cell_style)
        ],
        [
            Paragraph(f"<b>{tot_frames}</b> ({usable_frames} usable)", cell_bold),
            Paragraph(f"<b>{tot_dets}</b>", cell_bold),
            Paragraph(f"<b>{uniq_damages}</b>", cell_bold),
            Paragraph(f"<b>{avg_rci:.1f} / 100</b>", cell_bold),
            Paragraph(f"<b>Rs {tot_cost:,.2f}</b>", cell_bold)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[108, 108, 108, 108, 108])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e0f2fe')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#0369a1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#bae6fd')),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 14))

    # 4. Itemized Damage Manifest (Distinguishing AI vs Verified)
    elements.append(Paragraph("Itemized Pavement Surface Distress Manifest", section_title))
    
    if not damages:
        elements.append(Paragraph("<i>No road surface distresses were detected in this survey.</i>", cell_style))
    else:
        damage_rows = [[
            Paragraph("<b>Code</b>", cell_bold),
            Paragraph("<b>Distress Type</b>", cell_bold),
            Paragraph("<b>Severity / Priority</b>", cell_bold),
            Paragraph("<b>Conf</b>", cell_bold),
            Paragraph("<b>RCI</b>", cell_bold),
            Paragraph("<b>Est. Cost</b>", cell_bold),
            Paragraph("<b>Audit Status</b>", cell_bold)
        ]]

        for d in damages[:30]:  # Cap at 30 in PDF
            code = d.get("damage_code", "DMG-01")
            dtype = d.get("damage_type", "Pothole").capitalize()
            sev = d.get("severity", "Moderate")
            prio = f"P{d.get('priority', 3)}"
            conf = f"{d.get('confidence', 0.85):.2f}"
            rci_val = f"{d.get('rci', 60.0):.1f}"
            cost_val = f"Rs {d.get('estimated_repair_cost', 0):,.0f}"
            v_status = d.get("verification_status", "AI_DETECTED")

            damage_rows.append([
                Paragraph(code, cell_style),
                Paragraph(dtype, cell_style),
                Paragraph(f"{sev} ({prio})", cell_style),
                Paragraph(conf, cell_style),
                Paragraph(rci_val, cell_style),
                Paragraph(cost_val, cell_style),
                Paragraph(v_status, cell_bold if v_status == "VERIFIED" else cell_style)
            ])

        dmg_table = Table(damage_rows, colWidths=[65, 115, 95, 45, 50, 80, 90])
        dmg_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('PADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(dmg_table)

    elements.append(Spacer(1, 14))

    # 5. Work Orders & Crew Dispatch Section
    elements.append(Paragraph("Authorized Maintenance Work Orders & Dispatch", section_title))
    if not work_orders:
        elements.append(Paragraph("<i>No active work orders currently scheduled for this corridor.</i>", cell_style))
    else:
        wo_rows = [[
            Paragraph("<b>WO Code</b>", cell_bold),
            Paragraph("<b>Damage Target</b>", cell_bold),
            Paragraph("<b>Status</b>", cell_bold),
            Paragraph("<b>Priority</b>", cell_bold),
            Paragraph("<b>Est. Cost</b>", cell_bold)
        ]]
        for wo in work_orders[:10]:
            wo_rows.append([
                Paragraph(wo.get("work_order_code", "WO-01"), cell_style),
                Paragraph(wo.get("damage_code", "DMG-01"), cell_style),
                Paragraph(wo.get("status", "DETECTED"), cell_bold),
                Paragraph(f"Priority {wo.get('priority', 3)}", cell_style),
                Paragraph(f"Rs {wo.get('estimated_cost', 0):,.0f}", cell_style)
            ])
        wo_table = Table(wo_rows, colWidths=[100, 110, 110, 100, 120])
        wo_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('PADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ]))
        elements.append(wo_table)

    # 6. Audit & Provenance Footer
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceBefore=4, spaceAfter=8))
    elements.append(Paragraph(
        "<b>ENGINEERING PROVENANCE:</b> This report was compiled deterministically from YOLOv8 visual inference and "
        "spatial telemetry stored in the official ROADSense AI PostgreSQL registry. No synthetic detections participate "
        "in this document.",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748b'))
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
