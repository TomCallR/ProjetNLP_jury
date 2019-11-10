from datetime import date

import app

from sqlalchemy.orm import sessionmaker

from app.database.models import Course

app.db.models.Base.metadata.create_all(app.engine)

Session = sessionmaker(bind=app.engine)
session = Session()

da = Course(label='Data Analyst',
            startdate=date(2019, 3, 18),
            enddate=date(2019, 12, 2),
            spreadsheet='ProjetNLP')
session.add(da)
session.commit()

courses = session.query(Course).all()
print(courses)

