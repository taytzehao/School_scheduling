from Subject import Subject
from Teach import teach


class Teacher:
    instances = []
    def __init__(self,subject, teacher_name,hour_limit_perday=5,max_week=12):
        self.__class__.instances.append(self)
        self.hour_limit_perday=hour_limit_perday
        self.max_hours_per_week=max_week
        self.classes=[]
        self.assigned_hours=0
        self.teacher_name=teacher_name
        self.specialty_subject = subject


    def add_class(self,teach_activity):

        if isinstance(teach_activity,teach):
            self.classes.append(teach_activity)
        else:
            raise Error("Invalid teaching activity")

    def teach_schedule(self):
        schedule=[]
        for clas in self.classes:
            schedule.append([clas.day,clas.period])
        return schedule

    def hours_taught(self):
        return len(self.classes)

