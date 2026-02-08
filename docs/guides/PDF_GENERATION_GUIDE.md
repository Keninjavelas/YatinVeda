# PDF Generation Guide

## Overview

YatinVeda includes professional PDF generation capabilities for:
- **Remedy Prescriptions**: Customized PDFs with patient details, remedies, and guru signature
- **Birth Charts**: Astrological chart analysis with planetary positions and predictions
- **QR Code Integration**: Prescription verification via QR codes

## Architecture

### Components

1. **PrescriptionGenerator Module** (`backend/modules/prescription_generator.py`)
   - Generates professional PDFs using reportlab
   - Automatic fallback to text-based PDFs if reportlab unavailable
   - QR code generation with qrcode library
   - Support for embedding images and signatures

2. **Prescriptions API** (`backend/api/v1/prescriptions.py`)
   - Endpoint: `POST /api/v1/prescriptions`
   - Automatically generates PDFs on prescription creation
   - Stores PDF URLs and QR codes with prescription records

3. **User Charts API** (`backend/api/v1/user_charts.py`)
   - Endpoint: `GET /api/v1/charts/{chart_id}/pdf`
   - Generates on-demand chart PDFs with analysis

## Setup

### Install Dependencies

All required packages are in `requirements.txt`:

```bash
pip install -r backend/requirements.txt

# Key packages for PDF generation:
# - reportlab==4.0.9       (Professional PDF generation)
# - Pillow==10.1.0         (Image processing)
# - qrcode==7.4.2          (QR code generation)
```

## Features

### 1. Prescription PDF Generation

#### Automatic Generation

When a guru creates a prescription via the API:

```bash
POST /api/v1/prescriptions

{
  "patient_id": 123,
  "guru_id": 456,
  "title": "Mars Dosha Remedies",
  "diagnosis": "Mars is poorly placed in your chart...",
  "remedies": [
    {
      "category": "Gemstone",
      "description": "Wear a 5-carat red coral",
      "duration": "1 year",
      "frequency": "Daily"
    },
    {
      "category": "Mantra",
      "description": "Recite Mangal Mantra (Om Angarakaya Namah)",
      "duration": "40 days",
      "frequency": "3 times daily"
    }
  ],
  "notes": "Ensure the gemstone is set in copper or silver",
  "follow_up_date": "2024-12-31"
}
```

**Automatic Actions**:
- ✅ Generates professional PDF with all details
- ✅ Creates QR code for verification
- ✅ Saves files to `backend/generated_prescriptions/`
- ✅ Stores URLs in database
- ✅ Generates unique verification code

#### Prescription PDF Contents

```
┌─────────────────────────────────────────────────────────────┐
│           🌟 VEDIC REMEDY PRESCRIPTION 🌟                  │
├─────────────────────────────────────────────────────────────┤
│ Prescription ID: 12345 | Verification Code: ABC-XYZ-789    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ PATIENT INFORMATION                                         │
│ ─────────────────────────────────────────────────────────  │
│ Name: John Doe                                              │
│ Birth Date: January 15, 1990                                │
│ Birth Place: New York, USA                                  │
│                                                             │
│ PRESCRIBED BY                                               │
│ ─────────────────────────────────────────────────────────  │
│ Guru Name: Dr. Sharma                                       │
│ Specialization: Vedic Astrology                             │
│ Date: November 14, 2024                                     │
│                                                             │
│ DIAGNOSIS / ASTROLOGICAL ANALYSIS                           │
│ ─────────────────────────────────────────────────────────  │
│ Mars Dosha Remedies                                         │
│                                                             │
│ Your Mars is in the 7th house, indicating challenges in...  │
│                                                             │
│ PRESCRIBED REMEDIES                                         │
│ ─────────────────────────────────────────────────────────  │
│ 1. Gemstone: Wear a 5-carat red coral                       │
│    Duration: 1 year | Frequency: Daily                      │
│                                                             │
│ 2. Mantra: Recite Om Angarakaya Namah                       │
│    Duration: 40 days | Frequency: 3 times daily             │
│                                                             │
│ ADDITIONAL NOTES                                            │
│ ─────────────────────────────────────────────────────────  │
│ Ensure the gemstone is set in copper or silver              │
│                                                             │
│ FOLLOW-UP                                                   │
│ ─────────────────────────────────────────────────────────  │
│ Follow-up consultation: December 31, 2024                   │
│                                                             │
│ ─────────────────────────────────────────────────────────  │
│ Guru Signature: ____________________  Date: ______________  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Birth Chart PDF Generation

#### On-Demand Generation

```bash
GET /api/v1/charts/{chart_id}/pdf

# Returns a PDF with:
# - Planetary positions (all 9 grahas)
# - Key placements (Ascendant, Sun sign, Moon sign, Nakshatra)
# - Birth chart image (if available)
# - Astrological analysis/predictions
```

#### Chart PDF Contents

```
┌─────────────────────────────────────────────────────────────┐
│            🌙 VEDIC BIRTH CHART ANALYSIS 🌙                │
├─────────────────────────────────────────────────────────────┤
│ User: John Doe's Chart                                      │
│ Generated: November 14, 2024 at 03:45 PM                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [BIRTH CHART IMAGE - embedded if available]                 │
│                                                             │
│ PLANETARY POSITIONS                                         │
│ ──────────────────────────────────────────────────────────  │
│ Planet    │ Sign        │ House │ Degree                    │
│ ──────────┼─────────────┼───────┼──────────                 │
│ SUN       │ Leo         │ 5     │ 14.2°                     │
│ MOON      │ Pisces      │ 12    │ 22.8°                     │
│ MARS      │ Aries       │ 7     │ 18.5°                     │
│ ... (more planets)                                          │
│                                                             │
│ KEY PLACEMENTS                                              │
│ ──────────────────────────────────────────────────────────  │
│ Ascendant (Lagna): Taurus                                   │
│ Moon Sign (Rasi): Pisces                                    │
│ Sun Sign: Leo                                               │
│ Birth Star (Nakshatra): Revati                              │
│                                                             │
│ ASTROLOGICAL ANALYSIS                                       │
│ ──────────────────────────────────────────────────────────  │
│ Your Taurus Ascendant indicates a stable, grounded nature...│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. QR Code Integration

#### Prescription Verification

Each prescription includes a QR code that links to:
```
https://yatinveda.com/verify/{VERIFICATION_CODE}
```

#### Features:
- **Auto-generated**: When prescription is created
- **Verification**: Unique code prevents counterfeits
- **Easy sharing**: Users can screenshot or print QR code
- **Mobile-friendly**: Scanned with any smartphone camera

#### Example QR Code URL:
```
QR Code Data: https://yatinveda.com/verify/ABC-XYZ-789-DEF
When scanned → Verification page shows prescription details
```

## API Usage

### Create Prescription with Auto-PDF

```bash
curl -X POST "http://localhost:8000/api/v1/prescriptions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "guru_id": 2,
    "title": "Karma Remedies",
    "diagnosis": "Saturn aspects indicate karmic lessons...",
    "remedies": [
      {
        "category": "Charity",
        "description": "Donate to widows and elderly",
        "duration": "3 months",
        "frequency": "Weekly"
      }
    ],
    "follow_up_date": "2024-12-31"
  }'
```

**Response includes PDF URLs**:
```json
{
  "id": 1,
  "title": "Karma Remedies",
  "pdf_url": "/prescriptions/download/prescription_1_ABC-XYZ.pdf",
  "qr_code_url": "/prescriptions/qr/qr_1_ABC-XYZ.png",
  "verification_code": "ABC-XYZ-789"
}
```

### Download Prescription PDF

```bash
GET /api/v1/prescriptions/{prescription_id}/pdf

# Returns PDF file for download
# Content-Type: application/pdf
```

### Get Birth Chart PDF

```bash
GET /api/v1/charts/{chart_id}/pdf

# Returns PDF file with chart analysis
# Content-Type: application/pdf
```

## Customization

### Modify Prescription Styling

Edit `backend/modules/prescription_generator.py`:

```python
# Change colors
title_style = self.ParagraphStyle(
    'CustomTitle',
    fontSize=20,
    textColor=self.colors.HexColor('#YOUR_COLOR'),  # Change hex code
    # ... other styles
)
```

### Add Custom Sections

```python
def generate_prescription_pdf(self, ...):
    # Add after remedies section
    story.append(self.Paragraph("<b>SPECIAL INSTRUCTIONS</b>", heading_style))
    story.append(self.Paragraph("Your custom content here", styles['Normal']))
```

### Embed Images/Signatures

```python
# Add guru digital signature
if digital_signature_path and Path(digital_signature_path).exists():
    img = self.Image(digital_signature_path, width=1.5*self.inch)
    story.append(img)
```

## File Storage

### Directory Structure

```
backend/
├── generated_prescriptions/           # PDFs stored here
│   ├── prescription_1_CODE123.pdf
│   ├── prescription_2_CODE456.pdf
│   ├── qr_1_CODE123.png
│   └── qr_2_CODE456.png
└── modules/
    └── prescription_generator.py
```

### Storage Options

#### Local Filesystem (Current Default)
```python
prescriptions_dir = Path("backend/generated_prescriptions")
prescriptions_dir.mkdir(exist_ok=True)
with open(pdf_path, "wb") as f:
    f.write(pdf_bytes)
```

#### Cloud Storage (Optional Enhancement)

```python
# S3 Example (add boto3 to requirements)
import boto3

s3 = boto3.client('s3')
s3.put_object(
    Bucket='yatinveda-pdfs',
    Key=f'prescriptions/{filename}',
    Body=pdf_bytes,
    ContentType='application/pdf'
)
pdf_url = f"https://yatinveda-pdfs.s3.amazonaws.com/prescriptions/{filename}"
```

## Fallback Behavior

### reportlab Not Available

If reportlab is not installed, the system gracefully degrades:

1. **Text-Based PDFs**: Content is formatted as plain text
2. **QR Codes**: Placeholder images are generated
3. **Functionality**: All features still work, just less polished

### Example Fallback PDF

```
═══════════════════════════════════════════════════════════════════════════════
                        VEDIC REMEDY PRESCRIPTION
═══════════════════════════════════════════════════════════════════════════════

Prescription ID: 12345
Verification Code: ABC-XYZ-789
Date: November 14, 2024

───────────────────────────────────────────────────────────────────────────────
PATIENT INFORMATION
───────────────────────────────────────────────────────────────────────────────
Name: John Doe
Birth Date: January 15, 1990
Birth Place: New York, USA

[... rest of content ...]
```

## Performance Considerations

### PDF Generation Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Simple prescription PDF | ~100ms | reportlab is fast |
| Complex chart PDF | ~200-300ms | Depends on image embedding |
| QR code generation | ~50ms | qrcode library is optimized |

### Optimization Tips

1. **Async Generation**: Generate PDFs asynchronously
   ```python
   from celery import shared_task
   
   @shared_task
   def generate_pdf_async(prescription_id):
       # Generate PDF in background
   ```

2. **Caching**: Cache frequently requested PDFs
   ```python
   from redis import Redis
   redis = Redis()
   
   pdf_cache_key = f"pdf:prescription:{prescription_id}"
   if redis.exists(pdf_cache_key):
       return redis.get(pdf_cache_key)
   ```

3. **Cloud CDN**: Store PDFs in S3 with CloudFront
   - Faster downloads
   - Automatic scaling
   - Cost-effective for high volume

## Troubleshooting

### PDF file is corrupted

- Check file permissions in `backend/generated_prescriptions/`
- Verify disk space is available
- Ensure PDF generation didn't fail silently

### QR code not scanning

- Verify `verification_url` is correct
- Check QR code size (should be at least 200x200px)
- Try with different QR reader apps

### "reportlab is not installed"

```bash
pip install reportlab==4.0.9
pip install Pillow==10.1.0
```

### Images not embedding in PDF

- Check image file path exists
- Verify image format is supported (PNG, JPG, GIF)
- Use absolute file paths, not relative

### PDF too large

- Reduce image resolution before embedding
- Remove unnecessary images
- Compress using Ghostscript after generation

## Advanced Usage

### Custom Watermark

```python
def add_watermark(self, pdf_content: bytes, watermark_text: str) -> bytes:
    from reportlab.pdfgen import canvas
    from PyPDF2 import PdfReader, PdfWriter
    
    # Apply watermark logic
```

### Multi-Language Support

```python
def generate_prescription_pdf(self, ..., language='en'):
    if language == 'hi':
        title = "वैदिक उपचार प्रिप्ट"
    elif language == 'sa':
        title = "वैदिकोपचारप्रिप्ता"
    else:
        title = "VEDIC REMEDY PRESCRIPTION"
```

### Digital Signatures

```python
# Add guru's digital signature to PDF
import hashlib

signature_hash = hashlib.sha256(f"{prescription_id}{timestamp}".encode()).hexdigest()
# Embed in PDF for authenticity
```

## Production Checklist

- [ ] Test PDF generation with various prescription types
- [ ] Verify QR codes scan correctly
- [ ] Set up automated PDF cleanup/archival
- [ ] Configure cloud storage (S3, Azure Blob, etc.)
- [ ] Add PDF generation error monitoring
- [ ] Test fallback behavior without reportlab
- [ ] Verify file permissions and security
- [ ] Set up PDF download rate limiting
- [ ] Add PDF watermarking for security
- [ ] Test with high-volume prescription creation

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Test prescription PDF generation
3. Test chart PDF generation
4. Configure cloud storage if needed
5. Set up PDF caching for performance
6. Monitor PDF generation metrics
