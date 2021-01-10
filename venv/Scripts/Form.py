from Subject import Subject


class form():
    def __init__(self, Recess_period,period_num:list,subjects={},max_sub_pd=2,assembly=[0,0]):
        self.Recess_period=Recess_period
        self.assembly=assembly
        self.period_num=period_num
        self.max_sub_pd=max_sub_pd
        if subjects=={}:
            self.subjects={}
        else:
            self.subjects=subjects


    def add_subject(self,subject):
        if isinstance(subject,list) and all(isinstance(x,Subject) for x in subject):
            for sub in subject:
                self.subjects[sub.subject_name]=[sub.period_num]

        elif isinstance(subject,Subject):
            self.subjects[subject.subject_name]=[sub.period_num]
        else:
            raise Exception("Invalid subject object")

    def is_sufficient_classes(self):
        num_class=0
        for sub in self.subjects:
            num_class+=sub.period_num

        if sum(self.period_num)-6>num_class:
            return ("Too few class, classes less by {}".format(sum(self.period_num)-6-num_class))
        elif sum(self.period_num)-6<num_class:
            return("Too many class, classes extra by {}".format(sum(self.period_num)-6-num_class))
        else:
            return("right amount of class")

