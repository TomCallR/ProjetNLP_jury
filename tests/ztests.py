from datetime import date

import app

from sqlalchemy.orm import sessionmaker

from app.orm import Course

app.orm.Base.metadata.create_all(app.engine)

Session = sessionmaker(bind=app.engine)
session = Session()

da = Course(label='Data',
            startdate=date(2019, 3, 18),
            enddate=date(2019, 12, 2),
            spreadsheet='taratata')
session.add(da)
session.commit()

courses = session.query(Course).all()
print(courses)

