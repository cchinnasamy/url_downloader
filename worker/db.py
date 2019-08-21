from sqlalchemy import create_engine, schema, select, update, insert, and_, or_, delete, outerjoin, bindparam
from settings import DB_Conn_Str
from datetime import datetime

class DBConnection(object):
    
    def __init__(self,):
        self.engine = create_engine(DB_Conn_Str, pool_size=2, max_overflow=0, pool_recycle=3600, pool_pre_ping=True)
        self.metadata = schema.MetaData(bind=self.engine)
        self.scheduled_jobs = schema.Table('scheduled_jobs', self.metadata, autoload=True)

    def close(self):
        try:
            if self.engine:
                self.engine.dispose()
        except Exception as e:
            print(str(e))


    def insert_job(self,insert_value_dict):
        try:
            insert_value_dict["updated_time"]=datetime.utcnow()
            self.engine.execute(self.scheduled_jobs.insert(), [insert_value_dict])

        except Exception as e:
            print(str(e))

    def get_job(self,where_condition={}):
        try:
            where_clauses = [self.scheduled_jobs.c[key] == value
                             for (key, value) in where_condition.items()]
            info = (
                (select([self.scheduled_jobs])).where(and_(*where_clauses)))
            rs = info.execute()
            result = rs.fetchall()
            return result
        except Exception as e:
            print(str(e))
            return []

    def update_job(self,update_values_dict):
        try:
            update_values_dict["updated_time"]=datetime.utcnow()
            stmt = (self.scheduled_jobs.update().where(and_(
                self.scheduled_jobs.c.job_id == update_values_dict['job_id'])).values(update_values_dict))
            rs = stmt.execute()
            return {'status': 'success', 'message': 'updated products table details successfully'}

        except Exception as e:
            print(e)
            return {'status': 'failure', 'message': 'Error in updating products table'}
