#!/usr/bin/env python3
"""
Test script for PDF prescription generator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.prescription_generator import PrescriptionGenerator
from datetime import datetime

def test_prescription_pdf():
    """Test prescription PDF generation"""
    generator = PrescriptionGenerator()
    
    # Test data
    prescription_data = {
        'id': 'PRES-001',
        'title': 'Vedic Remedy for Career Growth',
        'diagnosis': 'Based on your birth chart analysis, Saturn in the 10th house is causing delays in career advancement. The following remedies will help strengthen your professional prospects.',
        'notes': 'Follow these remedies consistently for 40 days for best results.',
        'follow_up_date': '2025-02-15',
        'verification_code': 'VER-ABC123'
    }
    
    user_data = {
        'name': 'John Doe',
        'birth_date': '1990-05-15',
        'birth_place': 'Mumbai, India'
    }
    
    guru_data = {
        'name': 'Pandit Raj Kumar',
        'specialization': 'Vedic Astrology & Remedial Measures',
        'email': 'pandit@yatinveda.com'
    }
    
    remedies = [
        {
            'category': 'Gemstone Therapy',
            'description': 'Wear a Blue Sapphire (Neelam) of 3-5 carats in gold ring on the middle finger of right hand',
            'duration': '6 months minimum',
            'frequency': 'Daily wear after proper energization'
        },
        {
            'category': 'Mantra Chanting',
            'description': 'Chant "Om Sham Shanicharaya Namah" 108 times daily',
            'duration': '40 days',
            'frequency': 'Early morning before sunrise'
        },
        {
            'category': 'Charity & Service',
            'description': 'Donate black sesame seeds and mustard oil to poor on Saturdays',
            'duration': '7 consecutive Saturdays',
            'frequency': 'Weekly on Saturdays'
        }
    ]
    
    try:
        # Generate PDF
        pdf_bytes = generator.generate_prescription_pdf(
            prescription_data=prescription_data,
            user_data=user_data,
            guru_data=guru_data,
            remedies=remedies,
            notes="Please maintain a positive mindset and follow the remedies with devotion."
        )
        
        # Save to file for verification
        with open('test_prescription.pdf', 'wb') as f:
            f.write(pdf_bytes)
        
        print("✅ Prescription PDF generated successfully!")
        print(f"   File size: {len(pdf_bytes)} bytes")
        print(f"   Saved as: test_prescription.pdf")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating prescription PDF: {e}")
        return False

def test_chart_pdf():
    """Test chart PDF generation"""
    generator = PrescriptionGenerator()
    
    chart_data = {
        'ascendant': 'Leo',
        'sun_sign': 'Taurus',
        'moon_sign': 'Scorpio',
        'birth_star': 'Anuradha',
        'sun': {'sign': 'Taurus', 'house': '10', 'degree': '15.30'},
        'moon': {'sign': 'Scorpio', 'house': '4', 'degree': '22.45'},
        'mars': {'sign': 'Gemini', 'house': '11', 'degree': '8.15'},
        'mercury': {'sign': 'Aries', 'house': '9', 'degree': '28.20'},
        'jupiter': {'sign': 'Pisces', 'house': '8', 'degree': '12.10'},
        'venus': {'sign': 'Taurus', 'house': '10', 'degree': '5.55'},
        'saturn': {'sign': 'Aquarius', 'house': '7', 'degree': '18.30'},
        'rahu': {'sign': 'Gemini', 'house': '11', 'degree': '25.40'},
        'ketu': {'sign': 'Sagittarius', 'house': '5', 'degree': '25.40'}
    }
    
    predictions = """
    Based on your birth chart analysis:
    
    1. Career & Profession: With Sun in the 10th house in Taurus, you have strong potential for leadership roles in finance, real estate, or luxury goods. Saturn in the 7th house suggests partnerships will be crucial for your success.
    
    2. Relationships: Moon in Scorpio in the 4th house indicates deep emotional nature and strong family bonds. Venus in the 10th house brings harmony in professional relationships.
    
    3. Health: Mars in the 11th house provides good vitality and energy. However, be cautious about stress-related issues due to Moon-Saturn aspect.
    
    4. Spiritual Growth: Jupiter in the 8th house in Pisces indicates strong intuitive abilities and interest in occult sciences. This is an excellent placement for spiritual development.
    
    5. Remedies: Regular worship of Lord Shiva (for Moon-Saturn harmony) and Lord Vishnu (for Jupiter strength) is recommended.
    """
    
    try:
        pdf_bytes = generator.generate_chart_pdf(
            user_name="John Doe",
            chart_data=chart_data,
            predictions=predictions
        )
        
        # Save to file for verification
        with open('test_chart.pdf', 'wb') as f:
            f.write(pdf_bytes)
        
        print("✅ Chart PDF generated successfully!")
        print(f"   File size: {len(pdf_bytes)} bytes")
        print(f"   Saved as: test_chart.pdf")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating chart PDF: {e}")
        return False

def test_qr_code():
    """Test QR code generation"""
    generator = PrescriptionGenerator()
    
    try:
        verification_url = "https://yatinveda.com/verify/VER-ABC123"
        qr_buffer = generator.generate_qr_code(verification_url)
        
        # Save QR code
        with open('test_qr_code.png', 'wb') as f:
            f.write(qr_buffer.getvalue())
        
        print("✅ QR Code generated successfully!")
        print(f"   Saved as: test_qr_code.png")
        print(f"   URL encoded: {verification_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating QR code: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing PDF Prescription Generator...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # Test prescription PDF
    print("\n1. Testing Prescription PDF Generation:")
    if test_prescription_pdf():
        success_count += 1
    
    # Test chart PDF
    print("\n2. Testing Chart PDF Generation:")
    if test_chart_pdf():
        success_count += 1
    
    # Test QR code
    print("\n3. Testing QR Code Generation:")
    if test_qr_code():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All PDF generation features are working correctly!")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    print("\nGenerated files:")
    print("- test_prescription.pdf")
    print("- test_chart.pdf") 
    print("- test_qr_code.png")