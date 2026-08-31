from database import sync_engine,session_factory,async_session_factory
from models import WorkersORM, Base, ResumesORM,Workload
from sqlalchemy import insert, text,select, func, cast, Integer, and_
from sqlalchemy.orm import aliased, joinedload, selectinload
import asyncio

class SyncORM():

    @staticmethod
    def create_tables():
        
        Base.metadata.drop_all(sync_engine)
        Base.metadata.create_all(sync_engine)

    @staticmethod
    def insert_workers():
        with session_factory() as session:
            worker_Jack = WorkersORM(user_name='Jack')
            worker_Michael = WorkersORM(user_name='Michael')  
            session.add_all([worker_Jack,worker_Michael])
            session.commit()

    @staticmethod
    def select_workers():
        with session_factory() as session:
            # worker_id = 1
            # worker_Jack = session.get(WorkersORM,worker_id)
            query = select(WorkersORM)
            result = session.execute(query)
            workers = result.scalars().all()
            print(workers)
    @staticmethod
    def update_workers(worker_id:int = 2,new_username: str = 'Misha'):
        with session_factory() as session:
            worker_Michael = session.get(WorkersORM,worker_id)
            worker_Michael.user_name = new_username
            # session.expire_all()
            # session.refresh(worker_Michael)
            session.commit()

    @staticmethod
    def insert_resumes():
        with session_factory() as session:
            resume_jack_1 = ResumesORM(
                title="Python Junior Developer", compensation=50000, workload=Workload.fulltime, worker_id=1)
            resume_jack_2 = ResumesORM(
                title="Python Разработчик", compensation=150000, workload=Workload.fulltime, worker_id=1)
            resume_michael_1 = ResumesORM(
                title="Python Data Engineer", compensation=250000, workload=Workload.parttime, worker_id=2)
            resume_michael_2 = ResumesORM(
                title="Data Scientist", compensation=300000, workload=Workload.fulltime, worker_id=2)
            session.add_all([resume_jack_1, resume_jack_2, 
                             resume_michael_1, resume_michael_2])
            session.commit()

    @staticmethod
    def select_resumes_avg_compensation(language: str = 'Python'):
        with session_factory() as session:
            query = (
                select(
                    ResumesORM.workload,
                    cast(func.avg(ResumesORM.compensation), Integer).label('avg_comp')
                    ).select_from(ResumesORM)
                    .filter(and_(
                        ResumesORM.title.contains(language),
                        ResumesORM.compensation > 40000
                    ))
                    .group_by(ResumesORM.workload)
            )
            print(query.compile(compile_kwargs = {'literal_binds' : True}))
            res = session.execute(query)
            result = res.all()
            print(result)

    @staticmethod
    def select_workers_with_lazy_relationship():
        with session_factory() as session:
            query = (
                select(WorkersORM)
            )
            res = session.execute(query)
            result = res.scalars().all()

            worker1_resumes = result[0].resumes
            worker2_resumes = result[1].resumes

            print(worker1_resumes)
            print()
            print(worker2_resumes)
            print()
            print(result)

    @staticmethod
    def select_workers_with_join_relationship():
        with session_factory() as session:
            query = (
                select(WorkersORM)
                .options(joinedload(WorkersORM.resumes))
            )
            res = session.execute(query)
            result = res.unique().scalars().all()

            worker1_resumes = result[0].resumes
            worker2_resumes = result[1].resumes

            print(worker1_resumes)
            print()
            print(worker2_resumes)
            print()
            print(result)

    @staticmethod
    def show_workers_parttime():
        with session_factory() as session:
            query = (
                select(WorkersORM)
                .options(selectinload(WorkersORM.resumes_parttime))
            )

            res = session.execute(query)
            result = res.scalars().all()
            print(result)
class AsyncORM():
    @staticmethod
    async def insert_additional_resumes():
        async with async_session_factory() as session:
            workers = [
                {"user_name": "Artem"},  # Исправлено на user_name
                {"user_name": "Roman"},
                {"user_name": "Petr"},
            ]
            resumes = [
                {"title": "Python программист", "compensation": 60000, "workload": Workload.fulltime, "worker_id": 3},
                {"title": "Machine Learning Engineer", "compensation": 70000, "workload": Workload.parttime, "worker_id": 3},
                {"title": "Python Data Scientist", "compensation": 80000, "workload": Workload.parttime, "worker_id": 4},
                {"title": "Python Analyst", "compensation": 90000, "workload": Workload.fulltime, "worker_id": 4},
                {"title": "Python Junior Developer", "compensation": 100000, "workload": Workload.fulltime, "worker_id": 5},
            ]
            
            insert_workers = insert(WorkersORM).values(workers)
            insert_resumes = insert(ResumesORM).values(resumes)
            
            await session.execute(insert_workers)
            await session.execute(insert_resumes)
            await session.commit()

    @staticmethod
    async def join_cte_subquery_window_func(like_language: str = 'Python'):
        async with async_session_factory() as session:
            r = aliased(ResumesORM)
            w = aliased(WorkersORM)

            subq = (
                select(
                    r,
                    w,
                    func.avg(r.compensation).over(partition_by=r.workload).cast(Integer).label('avg_workload_compensation')
                )
                .join(w,r.worker_id == w.id).subquery('helper1')
            )
            cte = (
                select(
                    subq.c.id,
                    subq.c.user_name,
                    subq.c.compensation,
                    subq.c.workload,
                    subq.c.avg_workload_compensation,
                    (subq.c.compensation - subq.c.avg_workload_compensation).label("compensation_diff")
                )
                .cte('helper2')
            )
            query = (
                select(cte)
                .order_by(cte.c.compensation_diff.desc())
            )
            #print(query.compile(compile_kwargs = {'literal_binds' : True}))
            res = await session.execute(query)
            result = res.all()
            print(result)
    @staticmethod
    async def left_inner_join():
        async with async_session_factory() as session:
            query = (
                select(
                    WorkersORM.user_name, ResumesORM.title
                )
                .join(ResumesORM,WorkersORM.id == ResumesORM.worker_id,isouter=True)
                .filter(ResumesORM.id.is_(None))
            )
            res = await session.execute(query)
            result = res.all()
            print(result)

    @staticmethod
    async def window_query_and_subqery():
        async with async_session_factory() as session:
            r = aliased(ResumesORM)
            w = aliased(WorkersORM)

            subq = (
                select(
                    w.user_name,
                    r.title,
                    r.workload,
                    r.compensation,
                    func.max(r.compensation).over(partition_by=r.workload).label("max_workload_comp")
                )
                .join(r,w.id == r.worker_id)
                .subquery()
            )

            query = (
                select(
                    subq.c.user_name,
                    subq.c.title,
                    subq.c.workload,
                    subq.c.compensation,
                    subq.c.max_workload_comp,
                    (subq.c.compensation - subq.c.max_workload_comp).label("max_diff")
                    )
            )
            res = await session.execute(query)
            result = res.all()
            print(result)
    @staticmethod
    async def join_aliased_sub_cte():
        async with async_session_factory() as session:
            r = aliased(ResumesORM)
            w = aliased(WorkersORM)
            
            subq = (
                select(
                    w.user_name,
                    r.title,
                    r.workload,
                    r.compensation,
                    func.avg(r.compensation).over(partition_by=r.workload).cast(Integer).label('avg_comp_workload')
        
                )
                .join(r,w.id == r.worker_id)
                .subquery()
            )

            cte = (
                select(
                subq.c.user_name,
                subq.c.title,
                subq.c.workload,
                subq.c.compensation,
                subq.c.avg_comp_workload,
                ((subq.c.compensation * 100) / subq.c.avg_comp_workload)
                .label("percent_of_avg")
            )
            .cte("salary_pct")
            )

            query = (
                select(
                    cte.c.user_name,
                    cte.c.title, cte.c.workload, cte.c.compensation, cte.c.avg_comp_workload, cte.c.percent_of_avg
                )
                .filter(cte.c.percent_of_avg > 100)
                .order_by(cte.c.percent_of_avg.desc())
            )

            res = await session.execute(query)
            result = res.all()
            print(result)
    @staticmethod
    async def analytics_compensation():
        async with async_session_factory() as session:
            r = aliased(ResumesORM)
            w = aliased(WorkersORM)

            subq = (
                select(
                    w.user_name,
                    r.title,
                    r.compensation,
                    func.avg(r.compensation).over(partition_by=w.id).cast(Integer).label("worker_avg_comp")
                )
                 .join(r, w.id == r.worker_id)
                .subquery()
            )

            query = (
                select(
                    subq.c.user_name,
                    subq.c.title,
                    subq.c.compensation,
                    subq.c.worker_avg_comp,
                    (subq.c.compensation - subq.c.worker_avg_comp)
                )
            )
            res = await session.execute(query)
            result = res.all()
            print(result)
    @staticmethod
    async def low_prices_workers():
        async with async_session_factory() as session:
            r = aliased(ResumesORM)
            w = aliased(WorkersORM)
            
            cte = (
                select(
                    w.user_name,
                    r.title,
                    r.workload,
                    r.compensation,
                    func.dense_rank().over(partition_by=r.workload,order_by=r.compensation.asc()).label("price_rank")
                )
                .join(r,w.id == r.worker_id)
                .cte()
            )

            query = (
                select(
                    cte.c.user_name,
                    cte.c.title,
                    cte.c.workload,
                    cte.c.compensation,
                    cte.c.price_rank
                )
                .filter(cte.c.price_rank <= 2)
                .order_by(cte.c.workload, cte.c.price_rank)
            )

        
async def main():
    await AsyncORM.insert_additional_resumes()
    # await AsyncORM.join_cte_subquery_window_func()
    # await AsyncORM.left_inner_join()
    # await AsyncORM.window_query_and_subqery()
    # await AsyncORM.join_aliased_sub_cte()
if __name__ == "__main__":
    SyncORM.create_tables()
    SyncORM.insert_workers()
    SyncORM.insert_resumes()
    asyncio.run(main())
    # SyncORM.select_workers_with_lazy_relationship()
    SyncORM.show_workers_parttime()
    # SyncORM.select_workers_with_join_relationship()
    # SyncORM.select_resumes_avg_compensation()
    print("Готово!")