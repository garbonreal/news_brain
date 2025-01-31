from .database import Base, db


class WebsiteUrl(db.Model):
    __tablename__ = 'website_link'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    # content = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def get_news_by_date(start_time, end_time):
        news_link = WebsiteUrl.query.filter(WebsiteUrl.time >= start_time, WebsiteUrl.time <= end_time)
        return news_link

    @staticmethod
    def get_news_by_id(news_id):
        news_link = WebsiteUrl.query.filter(WebsiteUrl.id == news_id).first()
        return news_link