# Example using SQLAlchemy
from sqlalchemy import Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class PodcastEpisode(Base):
    __tablename__ = 'podcast_episodes'
    id = Column(String, primary_key=True)
    transcription = Column(Text)
    summary = Column(Text)

def get_engine():
    return create_engine('sqlite:///podcasts.db')

def create_tables():
    engine = get_engine()
    Base.metadata.create_all(engine)

def save_transcription_and_summary(episode_id, transcription, summary):
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    episode = PodcastEpisode(id=episode_id, transcription=transcription, summary=summary)
    session.merge(episode)
    session.commit()
    session.close()
