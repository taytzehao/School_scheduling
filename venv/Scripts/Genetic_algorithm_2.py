from deap import algorithms
from deap import base
from deap import creator
from deap import tools
import copy
from functools import reduce
import operator
import numpy as np
import random
from Teach import teach
from Subject import Subject
import time
from collections import Counter
from itertools import permutations
from operator import attrgetter


class genetical_sort2():
    def __init__(self,class_instances,subject_instances,teacher_instances,teach_instances):
        self.class_instance=copy.deepcopy(class_instances)
        self.subject_instance=copy.deepcopy(subject_instances)
        self.teacher_instance=copy.deepcopy(teacher_instances)
        self.teach_instance=copy.deepcopy(teach_instances)

        self.subject_dict_num=dict(zip(range(len(subject_instances)),[subj.subject_name for subj in subject_instances]))
        self.subject_dict_name=dict([i.subject_name,i] for i in self.subject_instance) ## Dict type to quicken subject object access

        self.teacher_dict_num=dict(zip(range(len(teacher_instances)),[x.teacher_name for x in teacher_instances]))
        self.teacher_dict_name=dict([i.teacher_name,i] for i in self.teacher_instance) ## Dict type to quicken teacher object access

        self.period_address,self.section_per_class=self.initialize_period_address()

    ## Must include teacher assignment evaluation, as number of variation of teacher increase, the lower the fitness
    def initialize_teacher_individual(self):
        individual_list = []

        for classs in self.class_instance:

            classs_copy = copy.deepcopy(classs)
            classs_copy = reduce(operator.add, classs_copy.schedule)
            classs_copy = list(filter(lambda element: element != "Recess period" and element != "Assembly", classs_copy))

            for subj in classs.subjects.keys():

                if self.subject_dict_name[subj].specialty==True:
                    temp_teach = random.choice([key for key,val in self.teacher_dict_num.items() if self.teacher_dict_name[val].specialty_subject.subject_name==subj])
                else:
                    temp_teach = random.choice(list(self.teacher_dict_num.keys()))
                individual_list.append(temp_teach)

        return individual_list

    def initialize_period_address(self):

        period_address_counter=0
        period_address_dictionary=dict()
        Section=[] ## Number of class section for each class. 2 periods of the same subjects joined together is considered as a section.
        # Everytime  subject changes is considered a different section.

        for classs in self.class_instance:

            ## Initialize the number of section for each class
            Number_of_section=0

            ## For every subjects assigned to a class
            for sub in list(classs.subjects.keys()):

                ## Look for subject information
                subject_object=next(i for i in self.subject_instance if i.subject_name==sub)

                ## Total number of subjects for the period
                period_remaining=subject_object.period_num

                if subject_object.side_by_side==True:

                    while period_remaining>0 and (period_remaining/2)>=1:

                        ## Initialize the period address to have subject name and 2 periods
                        period_address_dictionary[period_address_counter]=[sub,2]
                        period_remaining-=2
                        period_address_counter+=1
                        Number_of_section+=1

                    while period_remaining>0 :

                        ## Once there is only 1 remaining period, period address will be assigned periods
                        period_address_dictionary[period_address_counter]=[sub,1]
                        period_remaining-=1
                        period_address_counter+=1
                        Number_of_section+=1

                else:
                    while period_remaining>0 :
                        ## If the subject is not encouraged to have back to back classes, only assign address with 1 period
                        period_address_dictionary[period_address_counter]=[sub,1]
                        period_remaining-=1
                        period_address_counter+=1
                        Number_of_section+=1

            Section.append(Number_of_section)

        return period_address_dictionary,Section

    def initialize_schedule_individual(self):

        individual=[]

        for num,i in enumerate(self.section_per_class):

            ## Create a list with the section number for the class
            temp_list=list(range(sum(self.section_per_class[:num]), sum(self.section_per_class[:num]) + i))

            ## Shuffle the temp_list
            random.shuffle(temp_list)

            ## Concatenate temp_list into individual
            individual=individual+temp_list

        return individual

    def evaluate_teacher_assignment(self,individual):
        decoded_individual=np.array(individual)

        fitness=0
        individual_counter=0

        class_instance=copy.deepcopy(self.class_instance)
        teacher_instance=copy.deepcopy(self.teacher_instance)
        teacher_dict_name = dict([i.teacher_name, i] for i in teacher_instance)

        for classs in class_instance:
            for sub_name, period_remaining in classs.subjects.items():

                teacher_chosen=self.teacher_dict_num[decoded_individual[individual_counter]]
                teacher_chosen_object=teacher_dict_name[teacher_chosen]

                ##Check for specialty, decrease fitness if teacher assigned does not is not specialized in the subject
                if teacher_chosen_object.specialty_subject.subject_name!=sub_name and\
                    self.subject_dict_name[sub_name].specialty==True :

                    fitness-=1

                ## Increase assigned hours of teacher
                teacher_chosen_object.assigned_hours+=period_remaining[0]

                ## increase individual counter
                individual_counter += 1

        ## Decrease fitness if the assigned hours of teacher exceeds the maximum limit
        for teacher in teacher_instance:
            if teacher.assigned_hours>teacher.max_hours_per_week:
                fitness-=(teacher.assigned_hours-teacher.max_hours_per_week)

        return [fitness]

    def evaluate_schedule_assignment(self,individual):

        decoded_individual=np.array(individual)

        fitness=0
        individual_counter=0

        ## Subject_chosen_number is used to track the number of periods remaining for each section.
        ## This is used to determine whether the next session can be proceeded to
        Subject_chosen_number=0

        ## Deepcopy class instances as the classes would be used multiple times
        class_instance=copy.deepcopy(self.class_instance)
        subject_instance=copy.deepcopy(self.subject_instance)
        teacher_instance=copy.deepcopy(self.teacher_instance)
        teach_instance = copy.deepcopy(self.teach_instance)

        subject_dict_name=dict([i.subject_name,i] for i in subject_instance) ## Dict type to quicken subject object access
        teacher_dict_name = dict([i.teacher_name, i] for i in teacher_instance)

        for classs in class_instance:

            ##
            SBS_counter=Counter()

            for day_num,day in enumerate(classs.schedule):

                for period_num,period in enumerate(day):

                    if period!="Recess period" and period!="Assembly":

                        ## Change subject new section once Subject_chosen_number reaches 0. Update individual counter
                        if Subject_chosen_number==0:

                            Subject_chosen=self.period_address[decoded_individual[individual_counter]][0]
                            Subject_chosen_number=self.period_address[decoded_individual[individual_counter]][1]
                            Subject_chosen_object=subject_dict_name[Subject_chosen]
                            individual_counter += 1

                        ## Select teacher that is assigned to the subject for the class
                        teacher_chosen = classs.subjects[Subject_chosen][1]
                        teacher_chosen_object = teacher_dict_name[teacher_chosen]

                        ## increase individual counter
                        Subject_chosen_number-=1

                        ## Update teacher teach instance
                        teach_instance.append(teach(day=day_num, period=period_num, subject=Subject_chosen,
                                                    teacher_name=teacher_chosen))
                        ## update schedule
                        classs.schedule[day_num][period_num] = teach_instance[-1]

                        ## Decrease fitness if morning class is after recess
                        if Subject_chosen_object.morning_class == True and period_num > classs.Recess_period:
                            fitness -= 1

                        ## Decrease fitness if periods that are supposed to be side by side are not present side by side
                        if Subject_chosen_object.side_by_side == True:

                            ## If last period of the week
                            if day_num==len(classs.schedule)-1 and period_num==len(classs.schedule[-1])-1:
                                if isinstance(classs.schedule[day_num][period_num -1], str): ## If period before is "Recess"
                                    SBS_counter.update({Subject_chosen:1})
                                elif classs.schedule[day_num][period_num - 1].subject!=Subject_chosen:
                                    SBS_counter.update({Subject_chosen:1})
                            elif period_num==(len(day)-1):
                                if classs.schedule[day_num][period_num-1].subject !=Subject_chosen:
                                    SBS_counter.update({Subject_chosen:1})
                            elif isinstance(classs.schedule[day_num][period_num + 1], str):
                                if classs.schedule[day_num][period_num - 1].subject != Subject_chosen:
                                    SBS_counter.update({Subject_chosen:1})
                            elif isinstance(classs.schedule[day_num][period_num -1], str) or period_num==0:
                                if Subject_chosen_number==0:
                                    SBS_counter.update({Subject_chosen:1})
                            else:
                                if classs.schedule[day_num][period_num - 1].subject != Subject_chosen and \
                                        Subject_chosen_number==0:
                                    SBS_counter.update({Subject_chosen:1})


                        ## Decrease remaining class required for the subject
                        try:
                            classs.subjects[Subject_chosen][0] -= 1
                        except:
                            pass

                        ## Decrease fitness if teacher is occupied at the time
                        if next((True for lesson in teacher_chosen_object.classes if lesson.day==day_num and lesson.period==period_num ),False):
                            fitness -= 1

                        ## Assign teacher to the period
                        teacher_chosen_object.add_class(teach_instance[-1])


                ## count number of subjects for the day
                my_dict = Counter(i.subject for i in classs.schedule[day_num] if not isinstance(i,str))


                ## Check for maximum number of period of side by side subjects and no side by side subjects per day.
                ## Decrease fitness if the total period per day for the subject exceeds the limit.
                for teach_activity, total_period in my_dict.items():

                    Subject_object=next(i for i in subject_instance if i.subject_name == teach_activity)

                    if Subject_object.side_by_side == True and total_period > classs.max_sub_pd:

                        fitness -= (total_period - classs.max_sub_pd)

                    elif Subject_object.side_by_side == False and total_period > 1:
                        fitness -= (total_period - 1)

            ## Decrease fitness according to subject that are supposed to be taught
            fitness -= sum(filter(lambda k:k>=0,map(lambda x: abs(x[0]), list(classs.subjects.values()))))

            ## Decrease fitness if periods that are supposed to be side by side towards each other are not side by side.
            fitness-=sum(list(SBS_counter.values()))-len(SBS_counter)

        return [fitness]

    ## Swap the genetic position for each class
    def exchange_mutation(self,individual,indpb,period_number_list):

        for num,clas in enumerate(period_number_list):
            for i in range(10):
                if random.random() < indpb:

                    ## Sample 2 random elements
                    period_choice=random.sample(range(sum(period_number_list[:num]), sum(period_number_list[:num])+clas),2)

                    ## Store element in temporary variable
                    temp1=individual[period_choice[0]]
                    temp2 = individual[period_choice[1]]

                    ## Swap the elements
                    individual[period_choice[0]]=temp2
                    individual[period_choice[1]]=temp1

        return individual,

    ## Reverse a random section of each class
    def inversion_mutation(self, individual, indpb, period_number_list):

        for num, clas in enumerate(period_number_list):
            for i in range(1):
                if random.random() < indpb:

                    ## Randomly sample 2 positions
                    period_choice = random.sample(
                        range(sum(period_number_list[:num]), sum(period_number_list[:num]) + clas), 2)

                    ## Swap position if 0th choice is larger than 1st choice
                    if period_choice[0]>period_choice[1]:
                        period_choice[0],period_choice[1]=period_choice[1],period_choice[0]

                    ## Reverse the position
                    individual[period_choice[0]:period_choice[1]+1]=reversed(individual[period_choice[0]:period_choice[1]+1])


        return individual,

    ## Randomly sample x amount of elements in individual, permute through all possible arrangements of the sample,
    # and choose the best.
    def heuristic_mutation(self,individual, period_number_list,gamma=3):

        for num, clas in enumerate(period_number_list):

            Selected_element=[]
            Score=[]

            ## Select random sample of the class
            Selected_index=random.sample(range(sum(period_number_list[:num]), sum(period_number_list[:num]) + clas), gamma)

            ## Convert index to element
            for i in Selected_index:
                Selected_element.append(individual[i])

            temp_individual=copy.deepcopy(individual)

            Permutation_suggestion=list(permutations(Selected_element))

            for nummer,permut in enumerate(Permutation_suggestion):

                ## Place permutation sample into temporarily deepcopied individual
                for number,i in enumerate(Selected_index):
                    temp_individual[i]=permut[number]

                ## Remember the score of each permutation
                Score.append(self.evaluate_schedule_assignment(temp_individual)[0])

            ## Select permutation with highest fitness score
            for number,i in enumerate(Selected_index):
                individual[i]=Permutation_suggestion[Score.index(max(Score))][number]

        return individual,

    ## Assign teacher to the subject of each class
    def assign_teacher(self,solution):
        counter=0

        for classs in self.class_instance:
            for subject in list(classs.subjects.keys()):

                ## Assign the teacher for the subject
                classs.subjects[subject].append(self.teacher_dict_num[solution[counter]])

                teacher=next(teacher for teacher in self.teacher_instance if self.teacher_dict_num[solution[counter]]==teacher.teacher_name)
                teacher.assigned_hours+=classs.subjects[subject][0]

                counter+=1

    def print_invididual_to_schedule(self,individual):
        individual_counter = -1
        class_instance = copy.deepcopy(self.class_instance)
        subject_instance = copy.deepcopy(self.subject_instance)
        individual = np.array(individual)
        Subject_chosen_number=0

        for classs in self.class_instance:

            for day_num, day in enumerate(classs.schedule):
                for period_num, period in enumerate(day):

                    if not isinstance(classs.schedule[day_num][period_num],str):

                        if Subject_chosen_number==0:
                            individual_counter += 1
                            Subject_chosen_number=self.period_address[individual[individual_counter]][1]

                        classs.schedule[day_num][period_num] = self.period_address[individual[individual_counter]][0]
                        Subject_chosen_number-=1

                print("{},{}".format(day_num,classs.schedule[day_num]))
            print("")

    def print_teacher_assigned(self, teacher):
        counter = 0
        for classs in self.class_instance:
            print(classs.class_name)
            for sub_name in list(classs.subjects.keys()):
                print(sub_name, " : ", self.teacher_dict_num[teacher[counter]], end="   ")
                counter += 1

    def ID_mutation(self,individual,Mutation_material,indpb):
        for i in range(len(individual)):
            if random.random() < indpb:
                individual[i]=random.choice(Mutation_material)
        return individual,


    def main(self):

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        toolbox = base.Toolbox()

        toolbox.register("individual", tools.initIterate, creator.Individual, self.initialize_teacher_individual)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual, n=300)
        toolbox.register("populations", tools.initRepeat, list, toolbox.population)

        toolbox.register("evaluate", self.evaluate_teacher_assignment)
        toolbox.register("mate", tools.cxUniform, indpb=0.3)
        toolbox.register("mutate", self.ID_mutation,Mutation_material=list(range(len(self.teacher_instance))), indpb=0.1)
        toolbox.register("migrate", tools.migRing, k=30, selection=tools.selTournament,
                         replacement=tools.selRandom)
        toolbox.register("select", tools.selTournament, tournsize=2)
        pop = toolbox.population(n=300)
        pops = toolbox.populations(n=3)

        HALLOFFAME = tools.HallOfFame(1)

        stats = tools.Statistics(key=lambda ind: ind.fitness.values)

        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)

        pop, logbook = algorithms.eaSimple2(pops, toolbox, cxpb=0.5, mutpb=0.1, ngen=100,
                                           stats=stats, halloffame=HALLOFFAME, verbose=True)
        solution = next(indiv for indiv in pop if self.evaluate_teacher_assignment(indiv)[0] == 0)
        self.print_teacher_assigned(solution)
        print(solution)
        self.assign_teacher(solution)
        for teacher in self.teacher_instance:
            print(teacher.teacher_name, ":", teacher.assigned_hours)


        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        toolbox = base.Toolbox()

        toolbox.register("individual", tools.initIterate, creator.Individual, self.initialize_schedule_individual)

        toolbox.register("population", tools.initRepeat, list, toolbox.individual, n=300)
        toolbox.register("populations", tools.initRepeat, list, toolbox.population)

        toolbox.register("evaluate", self.evaluate_schedule_assignment)

        toolbox.register("mate", tools.cxOrdered_by_class,period_number_list=self.section_per_class)
        ##toolbox.register("mutate", self.exchange_mutation, indpb=0.1, period_number_list=self.section_per_class)
        ##toolbox.register("mutate", self.inversion_mutation, indpb=0.2, period_number_list=self.section_per_class)

        toolbox.register("mutate", self.heuristic_mutation, gamma=3,period_number_list=self.section_per_class)


        toolbox.register("migrate", tools.migRing, k=30, selection=tools.selTournament,
                         replacement=tools.selRandom)
        toolbox.register("select", tools.selTournament, tournsize=3)

        pop = toolbox.population(n=300)
        pops = toolbox.populations(n=3)

        HALLOFFAME = tools.HallOfFame(1)

        stats = tools.Statistics(key=lambda ind: ind.fitness.values)

        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)

        pop, logbook = algorithms.eaSimple2(pops, toolbox, cxpb=0.7, mutpb=0.3, ngen=1000,
                                           stats=stats, halloffame=HALLOFFAME, verbose=True)

        Valid_individual=max(pop,key=attrgetter("fitness"))
        
        self.print_invididual_to_schedule(Valid_individual)
