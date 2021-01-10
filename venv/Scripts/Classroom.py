from Form import form
from Teach import teach


class classroom(form):
    instances=[]
    def __init__(self,form_instance,class_name):
        self.class_name=class_name
        self.__class__.instances.append(self)
        instance_attrs = vars(form_instance)

        super().__init__(**instance_attrs)
        self.schedule = []
        for day, period_num in enumerate(self.period_num):
            self.schedule.append([0 for y in range(period_num)])
            self.schedule[day][self.Recess_period] = "Recess period"
        self.schedule[self.assembly[0]][self.assembly[1]] = "Assembly"






