import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from app import db, ListeningHistory
import logging

logger = logging.getLogger(__name__)

def load_data_from_csv(filepath):
    """Loads CSV data into the database."""
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        df['timestamp'] = pd.to_datetime(df['ts'])
        
        # Additional data processing can be added here
        
        batch_size = 1000
        total_rows = len(df)
        
        for start in range(0, total_rows, batch_size):
            end = min(start + batch_size, total_rows)
            batch = df.iloc[start:end]
            
            history_entries = []
            for _, row in batch.iterrows():
                history_entry = ListeningHistory(
                    timestamp=row['timestamp'],
                    username=row['username'],
                    # Add other fields as necessary
                )
                history_entries.append(history_entry)
            
            try:
                db.session.bulk_save_objects(history_entries)
                db.session.commit()
                logger.info(f"Processed {end}/{total_rows} rows")
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Error in batch {start}-{end}: {str(e)}")
        
        logger.info("Data loading completed successfully")
    except Exception as e:
        logger.error(f"Error loading CSV: {str(e)}")