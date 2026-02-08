"""
PDF prescription and chart generator for remedy prescriptions and Vedic birth chart visualizations
Uses reportlab for professional PDF generation with embedded signatures and QR codes
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import io
import json
from pathlib import Path


class PrescriptionGenerator:
    """Generate PDF prescriptions and charts for remedy recommendations"""
    
    def __init__(self):
        """Initialize prescription generator with reportlab"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
            from reportlab.lib import colors
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            
            self.letter_size = letter
            self.A4_size = A4
            self.inch = inch
            self.cm = cm
            self.SimpleDocTemplate = SimpleDocTemplate
            self.Paragraph = Paragraph
            self.Spacer = Spacer
            self.Table = Table
            self.TableStyle = TableStyle
            self.Image = Image
            self.PageBreak = PageBreak
            self.getSampleStyleSheet = getSampleStyleSheet
            self.ParagraphStyle = ParagraphStyle
            self.TA_CENTER = TA_CENTER
            self.TA_LEFT = TA_LEFT
            self.TA_RIGHT = TA_RIGHT
            self.TA_JUSTIFY = TA_JUSTIFY
            self.colors = colors
            self.canvas = canvas
            self.ImageReader = ImageReader
            
            self.reportlab_available = True
        except ImportError:
            self.reportlab_available = False
    
    def generate_prescription_pdf(
        self,
        prescription_data: Dict[str, Any],
        user_data: Dict[str, str],
        guru_data: Dict[str, str],
        remedies: List[Dict],
        notes: Optional[str] = None,
        digital_signature: Optional[str] = None
    ) -> bytes:
        """
        Generate professional PDF prescription document with reportlab
        
        Args:
            prescription_data: Dictionary with id, title, diagnosis, notes, follow_up_date, verification_code
            user_data: Dictionary with name, birth_date, birth_place
            guru_data: Dictionary with name, specialization, email
            remedies: List of remedy dictionaries with category, description, duration, frequency
            notes: Optional additional notes
            digital_signature: Optional digital signature URL or path
            
        Returns:
            PDF file content as bytes
        """
        if not self.reportlab_available:
            return self._generate_text_fallback_pdf(prescription_data, user_data, guru_data, remedies, notes)
        
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        
        # Create document
        doc = self.SimpleDocTemplate(
            pdf_buffer,
            pagesize=self.letter_size,
            topMargin=0.5 * self.inch,
            bottomMargin=0.5 * self.inch,
            leftMargin=0.75 * self.inch,
            rightMargin=0.75 * self.inch
        )
        
        # Get styles
        styles = self.getSampleStyleSheet()
        title_style = self.ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=self.colors.HexColor('#8B4513'),  # Saddle brown for Vedic theme
            spaceAfter=10,
            alignment=self.TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = self.ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=self.colors.HexColor('#654321'),  # Dark brown
            spaceAfter=6,
            spaceBefore=6,
            fontName='Helvetica-Bold'
        )
        
        # Build document content
        story = []
        
        # Header - Title
        story.append(self.Paragraph("🌟 VEDIC REMEDY PRESCRIPTION 🌟", title_style))
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Prescription metadata
        prescription_id = prescription_data.get('id', 'N/A')
        verification_code = prescription_data.get('verification_code', 'N/A')
        
        header_text = f"<b>Prescription ID:</b> {prescription_id} | <b>Verification Code:</b> {verification_code}"
        story.append(self.Paragraph(header_text, styles['Normal']))
        story.append(self.Spacer(1, 0.15 * self.inch))
        
        # Divider line using table
        divider = self.Table([['_' * 80]], colWidths=[7.5 * self.inch])
        divider.setStyle(self.TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(divider)
        story.append(self.Spacer(1, 0.15 * self.inch))
        
        # Patient and Guru Information
        patient_name = user_data.get('name', 'N/A')
        birth_date = user_data.get('birth_date', 'N/A')
        birth_place = user_data.get('birth_place', 'N/A')
        
        guru_name = guru_data.get('name', 'N/A')
        specialization = guru_data.get('specialization', 'Vedic Astrology')
        
        # Patient Section
        story.append(self.Paragraph("<b>PATIENT INFORMATION</b>", heading_style))
        patient_info = [
            [f"<b>Name:</b>", patient_name],
            [f"<b>Birth Date:</b>", birth_date],
            [f"<b>Birth Place:</b>", birth_place]
        ]
        patient_table = self.Table(patient_info, colWidths=[2 * self.inch, 4.5 * self.inch])
        patient_table.setStyle(self.TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(patient_table)
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Guru Section
        story.append(self.Paragraph("<b>PRESCRIBED BY</b>", heading_style))
        guru_info = [
            [f"<b>Guru Name:</b>", guru_name],
            [f"<b>Specialization:</b>", specialization],
            [f"<b>Date:</b>", datetime.now().strftime("%B %d, %Y")]
        ]
        guru_table = self.Table(guru_info, colWidths=[2 * self.inch, 4.5 * self.inch])
        guru_table.setStyle(self.TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(guru_table)
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Diagnosis
        title = prescription_data.get('title', 'Remedy Prescription')
        diagnosis = prescription_data.get('diagnosis', '')
        story.append(self.Paragraph("<b>DIAGNOSIS / ASTROLOGICAL ANALYSIS</b>", heading_style))
        story.append(self.Paragraph(f"<b>{title}</b>", styles['Normal']))
        if diagnosis:
            story.append(self.Paragraph(diagnosis, styles['BodyText']))
        story.append(self.Spacer(1, 0.15 * self.inch))
        
        # Remedies Section
        story.append(self.Paragraph("<b>PRESCRIBED REMEDIES</b>", heading_style))
        
        if remedies:
            for idx, remedy in enumerate(remedies, 1):
                category = remedy.get('category', 'General Remedy')
                description = remedy.get('description', '')
                duration = remedy.get('duration', '')
                frequency = remedy.get('frequency', '')
                
                remedy_text = f"<b>{idx}. {category}:</b> {description}"
                if duration or frequency:
                    remedy_text += f"<br/><i>Duration: {duration} | Frequency: {frequency}</i>"
                
                story.append(self.Paragraph(remedy_text, styles['BodyText']))
                story.append(self.Spacer(1, 0.1 * self.inch))
        else:
            story.append(self.Paragraph("No remedies prescribed at this time.", styles['Normal']))
        
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Additional Notes
        notes_text = notes or prescription_data.get('notes', '')
        if notes_text:
            story.append(self.Paragraph("<b>ADDITIONAL NOTES</b>", heading_style))
            story.append(self.Paragraph(notes_text, styles['BodyText']))
            story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Follow-up Information
        follow_up_date = prescription_data.get('follow_up_date', None)
        if follow_up_date:
            story.append(self.Paragraph("<b>FOLLOW-UP</b>", heading_style))
            story.append(self.Paragraph(f"Follow-up consultation scheduled for: <b>{follow_up_date}</b>", styles['Normal']))
            story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Footer / Signature
        story.append(self.Spacer(1, 0.3 * self.inch))
        signature_text = "_" * 40 + "  " + "_" * 40
        story.append(self.Paragraph(signature_text, styles['Normal']))
        story.append(self.Spacer(1, 0.05 * self.inch))
        sig_line = self.Table([
            ["Guru Signature", "Date"],
            ["", ""]
        ], colWidths=[3.75 * self.inch, 3.75 * self.inch])
        sig_line.setStyle(self.TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        story.append(sig_line)
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def _generate_text_fallback_pdf(
        self,
        prescription_data: Dict[str, Any],
        user_data: Dict[str, str],
        guru_data: Dict[str, str],
        remedies: List[Dict],
        notes: Optional[str] = None
    ) -> bytes:
        """Generate text-based fallback PDF when reportlab is not available"""
        content = f"""
═══════════════════════════════════════════════════════════════════════════════
                        VEDIC REMEDY PRESCRIPTION
═══════════════════════════════════════════════════════════════════════════════

Prescription ID: {prescription_data.get('id', 'N/A')}
Verification Code: {prescription_data.get('verification_code', 'N/A')}
Date: {datetime.now().strftime('%B %d, %Y')}

───────────────────────────────────────────────────────────────────────────────
PATIENT INFORMATION
───────────────────────────────────────────────────────────────────────────────
Name: {user_data.get('name', 'N/A')}
Birth Date: {user_data.get('birth_date', 'N/A')}
Birth Place: {user_data.get('birth_place', 'N/A')}

───────────────────────────────────────────────────────────────────────────────
PRESCRIBED BY
───────────────────────────────────────────────────────────────────────────────
Guru Name: {guru_data.get('name', 'N/A')}
Specialization: {guru_data.get('specialization', 'Vedic Astrology')}

───────────────────────────────────────────────────────────────────────────────
DIAGNOSIS / ASTROLOGICAL ANALYSIS
───────────────────────────────────────────────────────────────────────────────
{prescription_data.get('title', 'Remedy Prescription')}

{prescription_data.get('diagnosis', 'N/A')}

───────────────────────────────────────────────────────────────────────────────
PRESCRIBED REMEDIES
───────────────────────────────────────────────────────────────────────────────
"""
        for idx, remedy in enumerate(remedies, 1):
            content += f"\n{idx}. {remedy.get('category', 'Remedy')}\n"
            content += f"   Description: {remedy.get('description', '')}\n"
            if remedy.get('duration'):
                content += f"   Duration: {remedy.get('duration')}\n"
            if remedy.get('frequency'):
                content += f"   Frequency: {remedy.get('frequency')}\n"
        
        if notes:
            content += f"\n───────────────────────────────────────────────────────────────────────────────\n"
            content += f"ADDITIONAL NOTES\n"
            content += f"───────────────────────────────────────────────────────────────────────────────\n{notes}\n"
        
        content += f"""
═══════════════════════════════════════════════════════════════════════════════
                            GURU SIGNATURE
═══════════════════════════════════════════════════════════════════════════════
_________________________________          _________________________________
Signature                                  Date

═══════════════════════════════════════════════════════════════════════════════
This prescription is verified and authenticated with code: {prescription_data.get('verification_code', 'N/A')}
═══════════════════════════════════════════════════════════════════════════════
"""
        return content.encode('utf-8')
    
    def generate_qr_code(self, verification_url: str) -> io.BytesIO:
        """
        Generate QR code for prescription verification
        
        Args:
            verification_url: URL to encode in QR code (e.g., https://yatinveda.com/verify/CODE)
            
        Returns:
            BytesIO object containing PNG QR code image
        """
        try:
            import qrcode
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to buffer
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return buffer
        except ImportError:
            # Fallback if qrcode not available
            return self._generate_placeholder_qr()
    
    def _generate_placeholder_qr(self) -> io.BytesIO:
        """Generate a placeholder PNG when qrcode is not available"""
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple placeholder image
            img = Image.new('RGB', (200, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw a border
            draw.rectangle([10, 10, 190, 190], outline='black', width=2)
            draw.text((50, 85), "QR CODE", fill='black')
            draw.text((30, 110), "(Not Generated)", fill='black')
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer
        except ImportError:
            # If PIL not available, return minimal PNG
            return io.BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
    
    def generate_chart_pdf(
        self,
        user_name: str,
        chart_data: Dict[str, Any],
        chart_image_path: Optional[str] = None,
        predictions: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF for birth chart with astrological analysis
        
        Args:
            user_name: Name of the user
            chart_data: Dictionary with astrological details (sun_sign, moon_sign, ascendant, etc.)
            chart_image_path: Optional path to chart image to embed
            predictions: Optional astrological predictions text
            
        Returns:
            PDF file content as bytes
        """
        if not self.reportlab_available:
            return self._generate_text_chart_fallback(user_name, chart_data, predictions)
        
        pdf_buffer = io.BytesIO()
        
        doc = self.SimpleDocTemplate(
            pdf_buffer,
            pagesize=self.letter_size,
            topMargin=0.5 * self.inch,
            bottomMargin=0.5 * self.inch,
            leftMargin=0.75 * self.inch,
            rightMargin=0.75 * self.inch
        )
        
        styles = self.getSampleStyleSheet()
        title_style = self.ParagraphStyle(
            'ChartTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=self.colors.HexColor('#8B4513'),
            spaceAfter=10,
            alignment=self.TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = self.ParagraphStyle(
            'ChartHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=self.colors.HexColor('#654321'),
            spaceAfter=6,
            spaceBefore=6,
            fontName='Helvetica-Bold'
        )
        
        story = []
        
        # Title
        story.append(self.Paragraph("🌙 VEDIC BIRTH CHART ANALYSIS 🌙", title_style))
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # User Info
        story.append(self.Paragraph(f"<b>{user_name}'s Chart</b>", styles['Heading2']))
        story.append(self.Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Chart Image (if provided)
        if chart_image_path and Path(chart_image_path).exists():
            try:
                img = self.Image(chart_image_path, width=4 * self.inch, height=4 * self.inch)
                story.append(img)
                story.append(self.Spacer(1, 0.2 * self.inch))
            except Exception as e:
                print(f"Could not embed chart image: {e}")
        
        # Planetary Positions
        story.append(self.Paragraph("<b>PLANETARY POSITIONS</b>", heading_style))
        
        planets_data = [
            ["Planet", "Sign", "House", "Degree"]
        ]
        
        # Extract key placements from chart_data
        for key in ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']:
            if key in chart_data:
                planet_info = chart_data[key]
                if isinstance(planet_info, dict):
                    planets_data.append([
                        key.upper(),
                        planet_info.get('sign', 'N/A'),
                        planet_info.get('house', 'N/A'),
                        f"{planet_info.get('degree', 'N/A')}°"
                    ])
        
        planets_table = self.Table(planets_data, colWidths=[1.5 * self.inch, 1.5 * self.inch, 1.5 * self.inch, 1.5 * self.inch])
        planets_table.setStyle(self.TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors.HexColor('#654321')),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, self.colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.colors.white, self.colors.HexColor('#f0f0f0')])
        ]))
        story.append(planets_table)
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Chart Points
        story.append(self.Paragraph("<b>KEY PLACEMENTS</b>", heading_style))
        
        key_placements = [
            ["Element", "Value"]
        ]
        
        if 'ascendant' in chart_data:
            key_placements.append(["Ascendant (Lagna)", str(chart_data['ascendant'])])
        if 'moon_sign' in chart_data:
            key_placements.append(["Moon Sign (Rasi)", str(chart_data['moon_sign'])])
        if 'sun_sign' in chart_data:
            key_placements.append(["Sun Sign", str(chart_data['sun_sign'])])
        if 'birth_star' in chart_data:
            key_placements.append(["Birth Star (Nakshatra)", str(chart_data['birth_star'])])
        
        placements_table = self.Table(key_placements, colWidths=[3.5 * self.inch, 3 * self.inch])
        placements_table.setStyle(self.TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors.HexColor('#654321')),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, self.colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.colors.white, self.colors.HexColor('#f0f0f0')])
        ]))
        story.append(placements_table)
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Predictions
        if predictions:
            story.append(self.Paragraph("<b>ASTROLOGICAL ANALYSIS</b>", heading_style))
            story.append(self.Paragraph(predictions, styles['BodyText']))
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def _generate_text_chart_fallback(
        self,
        user_name: str,
        chart_data: Dict[str, Any],
        predictions: Optional[str] = None
    ) -> bytes:
        """Generate text-based fallback chart PDF"""
        content = f"""
═══════════════════════════════════════════════════════════════════════════════
                         VEDIC BIRTH CHART ANALYSIS
═══════════════════════════════════════════════════════════════════════════════

User: {user_name}
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

───────────────────────────────────────────────────────────────────────────────
KEY PLANETARY PLACEMENTS
───────────────────────────────────────────────────────────────────────────────
"""
        for key, value in chart_data.items():
            if isinstance(value, dict):
                content += f"\n{key.upper()}:\n"
                for k, v in value.items():
                    content += f"  {k}: {v}\n"
            else:
                content += f"{key.upper()}: {value}\n"
        
        if predictions:
            content += f"""
───────────────────────────────────────────────────────────────────────────────
ASTROLOGICAL ANALYSIS
───────────────────────────────────────────────────────────────────────────────
{predictions}
"""
        
        content += f"""
═══════════════════════════════════════════════════════════════════════════════
This chart is provided for astrological guidance and self-awareness purposes.
═══════════════════════════════════════════════════════════════════════════════
"""
        return content.encode('utf-8')

