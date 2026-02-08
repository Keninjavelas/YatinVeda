"""Seed sample data for development and testing.

Creates sample gurus, community posts, events, and other test data.
Run after migrations to populate development database.

Usage:
    python scripts/seed_data.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models.database import (
    Guru, CommunityPost, CommunityEvent, UserProfile, User
)
from modules.auth import get_password_hash


def create_sample_users(db):
    """Create sample users for testing."""
    users = []
    
    # Create 5 sample users
    for i in range(1, 6):
        user = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            password_hash=get_password_hash("password123"),
            full_name=f"Test User {i}",
            is_active=True,
            is_admin=False
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    print(f"✅ Created {len(users)} sample users")
    return users


def create_sample_gurus(db):
    """Create sample gurus with different specializations."""
    gurus_data = [
        {
            "name": "Pandit Rajesh Kumar",
            "title": "Vedic Astrology Expert",
            "bio": "25 years of experience in Vedic astrology, numerology, and palmistry. Specialized in career guidance and relationship compatibility.",
            "specializations": ["Vedic Astrology", "Numerology", "Palmistry", "Career Guidance"],
            "languages": ["Hindi", "English", "Sanskrit"],
            "experience_years": 25,
            "rating": 48,
            "total_sessions": 1250,
            "price_per_hour": 200000,  # ₹2000
            "personality_tags": ["Compassionate", "Traditional", "Detail-oriented"]
        },
        {
            "name": "Dr. Priya Sharma",
            "title": "Ayurvedic & Astrological Consultant",
            "bio": "Integration of Ayurveda and Jyotish for holistic healing. PhD in Ayurvedic Sciences with deep knowledge of medical astrology.",
            "specializations": ["Medical Astrology", "Ayurveda", "Remedial Measures", "Health Predictions"],
            "languages": ["Hindi", "English"],
            "experience_years": 18,
            "rating": 47,
            "total_sessions": 890,
            "price_per_hour": 250000,  # ₹2500
            "personality_tags": ["Analytical", "Healing-focused", "Scientific"]
        },
        {
            "name": "Swami Anand Das",
            "title": "Spiritual Guide & KP Astrologer",
            "bio": "Krishnamurti Paddhati expert with focus on timing of events. Combines spiritual counseling with precise predictions.",
            "specializations": ["KP Astrology", "Prashna Kundali", "Muhurta", "Spiritual Guidance"],
            "languages": ["Hindi", "English", "Bengali"],
            "experience_years": 30,
            "rating": 50,
            "total_sessions": 2100,
            "price_per_hour": 300000,  # ₹3000
            "personality_tags": ["Wise", "Patient", "Spiritual"]
        },
        {
            "name": "Lalita Devi",
            "title": "Relationship & Compatibility Specialist",
            "bio": "Expert in marriage matching, relationship compatibility, and love problem solutions using Vedic astrology.",
            "specializations": ["Marriage Matching", "Love Astrology", "Compatibility Analysis", "Relationship Counseling"],
            "languages": ["Hindi", "English", "Marathi"],
            "experience_years": 15,
            "rating": 46,
            "total_sessions": 650,
            "price_per_hour": 180000,  # ₹1800
            "personality_tags": ["Empathetic", "Practical", "Modern approach"]
        },
        {
            "name": "Acharya Vishnu Bhatt",
            "title": "Gemstone & Remedy Expert",
            "bio": "Specializes in gemstone recommendations, Vedic remedies, mantra suggestions, and puja rituals for problem resolution.",
            "specializations": ["Gemology", "Remedial Astrology", "Mantras", "Puja & Rituals"],
            "languages": ["Hindi", "English", "Gujarati"],
            "experience_years": 20,
            "rating": 45,
            "total_sessions": 780,
            "price_per_hour": 150000,  # ₹1500
            "personality_tags": ["Traditional", "Knowledgeable", "Remedy-focused"]
        }
    ]
    
    gurus = []
    for guru_data in gurus_data:
        guru = Guru(**guru_data)
        db.add(guru)
        gurus.append(guru)
    
    db.commit()
    print(f"✅ Created {len(gurus)} sample gurus")
    return gurus


def create_sample_posts(db, users):
    """Create sample community posts."""
    posts_data = [
        {
            "content": "Just had an amazing session with Pandit Rajesh Kumar! His insights about my career path were spot on. Highly recommended! 🙏",
            "post_type": "text",
            "tags": ["testimonial", "career", "vedic-astrology"],
            "is_public": True
        },
        {
            "content": "Does anyone have experience with Ayurvedic remedies for Saturn transit? Looking for natural solutions.",
            "post_type": "question",
            "tags": ["ayurveda", "saturn", "remedies"],
            "is_public": True
        },
        {
            "content": "Sharing my birth chart analysis. Would love to hear your thoughts on my Jupiter placement in 5th house! 📊",
            "post_type": "chart",
            "tags": ["birth-chart", "jupiter", "discussion"],
            "is_public": True
        },
        {
            "content": "Attended the full moon meditation event yesterday. The collective energy was incredible! Thank you to all organizers! 🌕✨",
            "post_type": "text",
            "tags": ["meditation", "community", "full-moon"],
            "is_public": True
        },
        {
            "content": "Looking for recommendations: Best time for starting a new business according to Muhurta? My chart suggests February but want expert opinion.",
            "post_type": "question",
            "tags": ["muhurta", "business", "timing"],
            "is_public": True
        }
    ]
    
    posts = []
    for i, post_data in enumerate(posts_data):
        # Assign posts to different users
        user_idx = i % len(users)
        post = CommunityPost(
            user_id=users[user_idx].id,
            **post_data,
            likes_count=i * 3 + 2,  # Varying like counts
            comments_count=i + 1
        )
        db.add(post)
        posts.append(post)
    
    db.commit()
    print(f"✅ Created {len(posts)} sample community posts")
    return posts


def create_sample_events(db, users):
    """Create sample community events."""
    now = datetime.utcnow()
    
    events_data = [
        {
            "title": "Full Moon Meditation & Jyotish Discussion",
            "description": "Join us for a collective meditation during the full moon, followed by an open discussion on lunar influences in Vedic astrology.",
            "event_type": "workshop",
            "event_date": now + timedelta(days=7),
            "is_online": True,
            "meeting_link": "https://meet.example.com/fullmoon",
            "max_participants": 50,
            "is_public": True
        },
        {
            "title": "Beginner's Guide to Reading Birth Charts",
            "description": "A comprehensive workshop for beginners covering the basics of chart reading, house systems, and planetary aspects.",
            "event_type": "workshop",
            "event_date": now + timedelta(days=14),
            "is_online": True,
            "meeting_link": "https://meet.example.com/chart-basics",
            "max_participants": 30,
            "is_public": True
        },
        {
            "title": "Navratri Celebrations & Vedic Rituals",
            "description": "Community gathering for Navratri celebrations with traditional puja, bhajans, and astrological significance discussions.",
            "event_type": "celebration",
            "event_date": now + timedelta(days=21),
            "location": "Community Hall, Delhi",
            "is_online": False,
            "max_participants": 100,
            "is_public": True
        },
        {
            "title": "Q&A with Expert Astrologers",
            "description": "Live Q&A session with our panel of expert astrologers. Ask your questions and get instant guidance!",
            "event_type": "qa_session",
            "event_date": now + timedelta(days=3),
            "is_online": True,
            "meeting_link": "https://meet.example.com/expert-qa",
            "max_participants": 100,
            "is_public": True
        },
        {
            "title": "Advanced Transit Analysis Workshop",
            "description": "Deep dive into current planetary transits and their impact. For intermediate to advanced practitioners.",
            "event_type": "workshop",
            "event_date": now + timedelta(days=28),
            "is_online": True,
            "meeting_link": "https://meet.example.com/transit-analysis",
            "max_participants": 25,
            "is_public": True
        }
    ]
    
    events = []
    for i, event_data in enumerate(events_data):
        # Assign events to different organizers
        organizer_idx = i % len(users)
        event = CommunityEvent(
            organizer_id=users[organizer_idx].id,
            **event_data
        )
        db.add(event)
        events.append(event)
    
    db.commit()
    print(f"✅ Created {len(events)} sample community events")
    return events


def create_user_profiles(db, users):
    """Create profiles for sample users."""
    bio_templates = [
        "Passionate about Vedic wisdom and spiritual growth. Love connecting with like-minded seekers! 🙏",
        "Beginner in astrology but eager to learn. Here to understand my birth chart better.",
        "Practicing Vedic astrology for 5 years. Happy to share knowledge and learn from others.",
        "Looking for guidance on life path and career decisions through Jyotish.",
        "Ayurveda and astrology enthusiast. Believer in holistic healing approaches."
    ]
    
    locations = ["Mumbai", "Delhi", "Bangalore", "Pune", "Kolkata"]
    
    interests_list = [
        ["Vedic Astrology", "Meditation", "Yoga"],
        ["Birth Chart Reading", "Palmistry", "Numerology"],
        ["Ayurveda", "Gemstones", "Remedies"],
        ["KP Astrology", "Prashna", "Muhurta"],
        ["Spiritual Growth", "Mantras", "Vedic Rituals"]
    ]
    
    profiles = []
    for i, user in enumerate(users):
        profile = UserProfile(
            user_id=user.id,
            bio=bio_templates[i],
            location=locations[i],
            interests=interests_list[i],
            privacy_settings={
                "show_birth_chart": i % 2 == 0,
                "show_location": True,
                "allow_messages": True
            }
        )
        db.add(profile)
        profiles.append(profile)
    
    db.commit()
    print(f"✅ Created {len(profiles)} user profiles")
    return profiles


def main():
    """Seed all sample data."""
    print("Starting data seeding...")
    
    db = SessionLocal()
    try:
        # Check if admin exists (assuming bootstrap was run)
        admin = db.query(User).filter(User.is_admin == True).first()
        if not admin:
            print("⚠️  Warning: No admin user found. Run init_admin.py first.")
        
        # Create sample data
        users = create_sample_users(db)
        create_user_profiles(db, users)
        create_sample_gurus(db)
        create_sample_posts(db, users)
        create_sample_events(db, users)
        
        print("\n✅ Data seeding completed successfully!")
        print(f"   - {len(users)} users created")
        print(f"   - 5 gurus created")
        print(f"   - 5 community posts created")
        print(f"   - 5 events created")
        print(f"   - {len(users)} user profiles created")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
