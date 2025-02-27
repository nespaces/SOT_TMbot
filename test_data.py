from datetime import datetime, timedelta
from models.database import session_scope
from models.listing import Listing

def create_test_listing():
    """Create a test listing in SQLite database."""
    with session_scope() as session:
        # First, deactivate all existing listings for the test user
        test_user_id = 300240116
        existing_listings = session.query(Listing).filter(
            Listing.user_id == test_user_id,
            Listing.is_active == 1
        ).all()

        for listing in existing_listings:
            listing.is_active = 0
        session.commit()

        # Create a new listing
        listing = Listing(
            user_id=test_user_id,
            nickname='TestUser',
            gender='Мужской',
            age=25,
            experience=100,
            role='Рулевой',
            faction='Торговый союз',
            server='Европа',
            ship_type='Галеон',
            platform='PC',
            additional_info='Тестовая запись',
            contacts='@test_user',
            search_type='party',
            search_goal='PvE',
            status='approved',
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=1),
            is_active=1,  # SQLite boolean true is 1
            moderation_type='manual'
        )
        session.add(listing)
        session.commit()

if __name__ == '__main__':
    create_test_listing()