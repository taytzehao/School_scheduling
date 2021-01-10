import copy
from Teach import teach
import random
import math
import numpy as np

class heuristic():
    def __init__(self,class_instances,subject_instances,teacher_instances,teach_instances):
        self.class_instance=copy.deepcopy(class_instances)

        self.subject_instance=copy.deepcopy(subject_instances)
        self.subject_dict=dict([i.subject_name,i] for i in self.subject_instance) ## Dict type to quicken subject object access

        self.teacher_instance=copy.deepcopy(teacher_instances)
        self.teacher_dict=dict([i.teacher_name,i] for i in self.teacher_instance) ## Dict type to quicken teacher object access

        self.tach_instance=copy.deepcopy(teach_instances)

    def teacher_assignment(self):

        for every_classroom in self.class_instance:
            for every_subject, teach_val in every_classroom.subjects.items():
                temp_sub = self.subject_dict[every_subject]

                ## Assign teachers to subjects that require specialty knowledge first.
                if temp_sub.specialty == True:

                    ## Assign candidate teacher that have specialty knowledge in the subject and have sufficient teaching hours
                    candidate = [teachers for teachers in self.teacher_instance if
                                           teachers.specialty_subject.subject_name == temp_sub.subject_name
                                           and (teachers.assigned_hours + temp_sub.period_num) < teachers.max_hours_per_week]
                    self.assign_teacher(classs=every_classroom, candidate=candidate, subject=every_subject)

        for every_classroom in self.class_instance:
            for every_subject, teach_val in every_classroom.subjects.items():
                temp_sub = self.subject_dict[every_subject]

                if temp_sub.specialty == False:

                    ## Choose teacher candidate only based on hour availability
                    candidate = [teachers for teachers in self.teacher_instance if
                                 (teachers.assigned_hours + temp_sub.period_num) < teachers.max_hours_per_week]

                    self.assign_teacher(classs=every_classroom,candidate=candidate,subject=every_subject)


    def assign_teacher(self,classs,candidate,subject):
        random_teacher = random.choice(candidate)
        classs.subjects[subject].append(random_teacher.teacher_name)
        random_teacher.assigned_hours += self.subject_dict[subject].period_num

    ## Function to calculate whether there is sufficient teacher manpower. Includes manpower calculation for niche subjects.
    def teacher_sufficient(self):
        Specialty_Subject_dict = {}
        Non_Specialty_Subject_hours = 0
        for subject in self.subject_instance:
            if subject.specialty == True:
                Specialty_Subject_dict[subject.subject_name] = 0

        for classes in self.class_instance:
            for subject, val in classes.subjects.items():
                temp_sub = self.subject_dict[subject]
                if temp_sub.specialty == True:
                    Specialty_Subject_dict[subject] -= temp_sub.period_num
                else:
                    Non_Specialty_Subject_hours -= temp_sub.period_num

        for teacher in self.teacher_instance:
            Specialty_Subject_dict[teacher.specialty_subject.subject_name] += teacher.max_hours_per_week

        Lack_teacher_list = [(k, v) for k, v in Specialty_Subject_dict.items() if v < 0]
        if not len(Lack_teacher_list) == 0:
            print("The following subjects still lacks hours {}".format(Lack_teacher_list))

        Non_specialty_hours_available = sum(v for k, v in Specialty_Subject_dict.items() if v >= 0)

        if Non_specialty_hours_available > Non_Specialty_Subject_hours:
            print(
                "There is sufficient Non-specialty hours. There are still {} hours available while there is only {} hours required".format(
                    Non_specialty_hours_available, Non_Specialty_Subject_hours))
        else:
            print(
                "There is not sufficient Non-specialty hours. There are still {} hours available while there is only {} hours required".format(
                    Non_specialty_hours_available, Non_Specialty_Subject_hours))

    def print_teacher_assigned(self):
        for classes in self.class_instance:
            print(classes.class_name)
            for subject,teacher in classes.subjects.items():
                print("{}:{}".format(subject,teacher),end=" , ")
            print("\n")


    def random_sort(self):

        ## Classes are assigned based on the sequence of
        ## 1) Mandatory to be in the morning
        ## 2) Requires 2 consecutive periods
        ## 3) Assign single period classes
        ## In order to reduce the need to swap blanks at the end as period space requirement is needed.

        for classes in self.class_instance:
            for every_subject,teach_val in classes.subjects.items():
                subject_chosen_object=self.subject_dict[every_subject]
                if subject_chosen_object.morning_class==True:

                    while classes.subjects[every_subject][0]>1:

                        ## select only morning classes with double period as physical classes can only be performed with double period
                        day_coordinate,period_coordinate=random.choice(self.day_period_set(classs=classes,subject_name=every_subject,number_of_period=2,morning=True))
                        self.class_assignment(classs=classes, day_num=day_coordinate, period_num=period_coordinate,
                                                  subject=every_subject, total_period=2)

        for classes in self.class_instance:
            for every_subject, teach_val in classes.subjects.items():

                subject_chosen_object=self.subject_dict[every_subject]

                if subject_chosen_object.side_by_side==True:
                    while classes.subjects[every_subject][0] > 1:

                        ## Select classes that need to be side by side to each other
                        period_options = self.day_period_set(classs=classes, subject_name=every_subject,number_of_period=2)
                        day_coordinate,period_coordinate= random.choice(period_options)

                        self.class_assignment(classs=classes, day_num=day_coordinate, period_num=period_coordinate,
                                                  subject=every_subject, total_period=2)

        for classes in self.class_instance:
            for every_subject, teach_val in classes.subjects.items():

                subject_chosen_object=self.subject_dict[every_subject]

                if subject_chosen_object.side_by_side==False or subject_chosen_object.side_by_side==True:

                    while classes.subjects[every_subject][0] != 0:

                        ## Select coordinate for period that can be independent
                        period_options=self.day_period_set(classs=classes, subject_name=every_subject, number_of_period=1)
                        day_coordinate, period_coordinate = random.choice(period_options)
                        
                        self.class_assignment(classs=classes,day_num=day_coordinate,period_num=period_coordinate,subject=every_subject,total_period=1)



    def class_assignment(self,classs,day_num,period_num,subject,total_period):
        teacher_chosen_object = self.teacher_dict[classs.subjects[subject][1]]

        for i in range(total_period):
            self.tach_instance.append(teach(day=day_num, period=period_num+i, subject=subject, teacher_name=teacher_chosen_object.teacher_name))


            classs.schedule[day_num][period_num+i] = self.tach_instance[-1] ## Allocate class schedule with teach instance
            teacher_chosen_object.add_class(self.tach_instance[-1]) ## Allocate teacher with teach instance
            classs.subjects[subject][0] -= 1 ## Reduce hours remaining for the class' subject

    def day_period_set(self,classs,subject_name, number_of_period,morning=False):   ## Function to identify periods that can be assigned to the subject
        empty=True
        while empty:
            day_period=[]
            for day_num,day in enumerate(classs.schedule):

                ## A session is the number of period to teach for each class until the day end or recess period start. This is used to make consecutive periods select
                ## coordinates that are not odd.
                session = self.session_length(classs,[day_num,0])
                session_num = 0

                ## subjects taught for the day
                subjects_taught = [period.subject for period in day if isinstance(period, teach)]

                ## Teacher assigned object for class given the subject parameter
                teacher_chosen_object = self.teacher_dict[classs.subjects[subject_name][1]]

                ## Proceed only if the subject parameter is not taught on that day
                if not next((subject for subject in subjects_taught if subject == subject_name), False):

                    for period_num,period in enumerate(day):

                        ## Break loop for periods that are required to be in the morning if the period is already after recess
                        if morning == True:
                            if period_num > classs.Recess_period:
                                continue

                        blank_coordinates = []

                        for i in range(number_of_period):
                            if period_num != len(day) - 1:
                                blank_coordinates.append([day_num, period_num + i])

                        ## Period cannot be recess, assembly or more than the possible last period of the day
                        if period != "Recess period" and period != "Assembly" and period_num<=(len(day)-number_of_period):

                            ## Teacher must be free in the period that will be assigned
                            if not any(x in teacher_chosen_object.teach_schedule() for x in blank_coordinates):

                                ## Period coordinate cannot be in an odd coordinate if session is odd for classes that require 2 side by side periods.
                                if not (number_of_period==2 and session%2==0 and session_num%2==1):

                                    ## Append to day_period variable if the coordinate is blank
                                    if classs.schedule[day_num][period_num:period_num+number_of_period]==[0]*number_of_period:

                                        day_period.append([day_num,period_num])

                            session_num+=1
                        else:
                            ## Reset session if it is recess or assembly
                            session = self.session_length(classs, [day_num, period_num])
                            session_num=0

            ## No period fulfill the requirements, swap the remaining blank period with already assigned classes
            if not day_period:
                Available_blank_coordinate = random.choice(self.list_element_index(lis=classs.schedule, value=0, consecutive_number=number_of_period))
                self.swap_blanks(classs=classs, subject_name=subject_name, blank_coordinate=Available_blank_coordinate, number_of_period=number_of_period)
                empty=True
            else:
                empty=False

        return day_period

    def session_length(self,classs,coordinate):
        period_num=coordinate[1]

        if isinstance(classs.schedule[coordinate[0]][coordinate[1]],str):
            period_num+=1
        length=0
        for i in classs.schedule[coordinate[0]][period_num:]:


            if isinstance(i,str):
                return length
            length += 1

        return length

    ## Select the given blank coordinate and swap it with periods that are already assigned classes
    def swap_blanks(self,classs,subject_name, blank_coordinate,number_of_period):
        swap_coordinate = []
        subjects_taught_blank=[period.subject for period in classs.schedule[blank_coordinate[0]] if isinstance(period, teach)]
        blank_teacher_object = self.teacher_dict[classs.subjects[subject_name][1]]

        for day_num, day in enumerate(classs.schedule):

            subjects_taught = [period.subject for period in day if isinstance(period, teach)]

            ## Check if subject is taught on that day, proceed if it is not taught on that day

            if not next((subject for subject in subjects_taught if subject == subject_name), False):

                for period_num,period in enumerate(day):
                    if isinstance(period, teach):

                        ## Check if subject of that day is taught at the blank day, proceed if it is not taught on the blank day
                        if not next((subject for subject in subjects_taught_blank if subject == period.subject), False):


                            period_teacher_object = self.teacher_dict[classs.subjects[period.subject][1]]

                            blank_coordinates=[]
                            selected_coordinates=[]
                            for i in range(number_of_period):
                                if period_num!=len(day)-1:
                                    blank_coordinates.append([blank_coordinate[0],blank_coordinate[1]+i])
                                    selected_coordinates.append([day_num,period_num+i])

                            ## Check both the teacher of the period and blank period are not busy at that time
                            if not any(x in period_teacher_object.teach_schedule() for x in blank_coordinates) and not any(x in blank_teacher_object.teach_schedule() for x in selected_coordinates):

                                ## If the previous period is assembly or recess period
                                if isinstance(classs.schedule[day_num][period_num-1],str):
                                    if not period_num==len(classs.schedule[day_num])-1: ## Check if not last period of the day
                                        if isinstance(classs.schedule[day_num][period_num+1],teach): ## Check if next period is already assigned a class.
                                            if classs.schedule[day_num][period_num+1].subject!=classs.schedule[day_num][period_num].subject:
                                                swap_coordinate.append([day_num,period_num]) ## Append coordinate if next period is a different subject of single period parameter.
                                            else:
                                                if number_of_period==2:
                                                    swap_coordinate.append([day_num,period_num]) ## Append coordinate if next period is same subject for double period

                                ## If last period of the day and only swapping 1 period, append the coordinate
                                elif period_num==len(day)-1:
                                    if number_of_period==1:
                                        if classs.schedule[day_num][period_num - 1].subject != classs.schedule[day_num][
                                            period_num].subject:
                                            swap_coordinate.append([day_num,period_num])

                                ## If next period is Recess, append coordinate if the parameter period is single and the class before this is not the same subject
                                elif isinstance(classs.schedule[day_num][period_num+1],str):
                                    if number_of_period == 1:
                                        if isinstance(classs.schedule[day_num][period_num-1],teach):
                                            if classs.schedule[day_num][period_num-1].subject!=classs.schedule[day_num][period_num].subject:
                                                swap_coordinate.append([day_num,period_num])

                                else:
                                    if isinstance(classs.schedule[day_num][period_num - 1], teach) and isinstance(classs.schedule[day_num][period_num + 1], teach):

                                        ## If single period parameter, check if theere are no same subject after and before the coordinate, to only append single period
                                        if number_of_period == 1:
                                            if classs.schedule[day_num][period_num-1].subject!=classs.schedule[day_num][period_num].subject and classs.schedule[day_num][period_num+1].subject!=classs.schedule[day_num][period_num].subject:
                                                swap_coordinate.append([day_num,period_num])
                                        ## If double period parameter, append swap coordinate only if next period is of the same subject
                                        if number_of_period==2:
                                            if classs.schedule[day_num][period_num+1].subject==classs.schedule[day_num][period_num].subject:
                                                swap_coordinate.append([day_num, period_num])


        swap_coordinate=random.choice(swap_coordinate)

        ## Assign blank coordinates with the classes at the randomly selected swap_coordinate
        classs.schedule[blank_coordinate[0]][blank_coordinate[1]:blank_coordinate[1]+number_of_period]=classs.schedule[swap_coordinate[0]][swap_coordinate[1]:swap_coordinate[1]+number_of_period]
        for i in range(number_of_period):
            classs.schedule[blank_coordinate[0]][blank_coordinate[1]].day=blank_coordinate[0]
            classs.schedule[blank_coordinate[0]][blank_coordinate[1]+i].period=blank_coordinate[1]+i

        ## Assign blanks to the swap coordinate
        classs.schedule[swap_coordinate[0]][swap_coordinate[1]:swap_coordinate[1]+number_of_period]=[0]*number_of_period

    ## consecutive_number parameter to identify coordinate that requires the blank period coordinate to be side by side towards each other
    def list_element_index(self, lis,value,consecutive_number):
        index=[]
        for x_axis, day in enumerate(lis):
            for y_axis,period in enumerate(day):
                if y_axis<=len(day)-consecutive_number:
                    if lis[x_axis][y_axis:y_axis+consecutive_number]==[value]*consecutive_number:
                        index.append([x_axis,y_axis])
        return index

    def print_schedule(self):
        for classs in self.class_instance:
            print(classs.class_name)
            for day in classs.schedule:
                for period in day:
                    if isinstance(period,str) or isinstance(period,int):
                        print(period,end=", " )
                    else:
                        print(period.subject,end=", ")
                print("")
            print("")