from deap import algorithms
from deap import base
from deap import creator
from deap import tools
import copy
from functools import reduce
import numpy as np
import operator
import random
from Teach import teach
from Subject import Subject
import time
from collections import Counter


class genetical_sort():
    def __init__(self,class_instances,subject_instances,teacher_instances,teach_instances):
        self.class_instance=class_instances
        self.subject_instance=subject_instances
        self.teacher_instance=teacher_instances
        self.tach_instance=teach_instances
        self.subject_dict=dict(zip(range(len(subject_instances)),[subj.subject_name for subj in subject_instances]))
        self.teacher_dict=dict(zip(range(len(teacher_instances)),[x.teacher_name for x in teacher_instances]))
        self.subject_total=len(self.subject_dict)
        self.teacher_total=len(self.teacher_dict)
        self.subject_bit_length=self.subject_total.bit_length()
        self.teacher_bit_length=self.teacher_total.bit_length()
        self.period_number_list=self.initialize_period_num_per_class()
        self.subject_number_list=self.initialize_subject_num_per_class()

    def initialize_individual(self):
        individual_list=[]


        for classs in self.class_instance:
            classs_copy=copy.deepcopy(classs)
            classs_copy=reduce(operator.add,classs_copy.schedule)
            classs_copy = list(filter(lambda element: element!="Recess period" and element!="Assembly", classs_copy))

            for num,period in enumerate(classs_copy):

                temp_sub=random.choice(list(self.subject_dict.keys()))
                temp_teach=random.choice(list(self.teacher_dict.keys()))
                '''
                temp_sub=bin(temp_sub).replace("0b", "").zfill(self.subject_bit_length)
                temp_teach = bin(temp_teach).replace("0b", "").zfill(self.teacher_bit_length)
                classs_copy[num]=temp_sub+temp_teach
                '''
                individual_list.append([temp_sub , temp_teach])

        '''
        for classs in self.class_instance:
            classs_copy = copy.deepcopy(classs)
            classs_copy = reduce(operator.add, classs_copy.schedule)
            classs_copy = list(filter(lambda element: element!="Recess period" and element!="Assembly", classs_copy))
            classs_copy=list(map(lambda x: random.choice(list(self.subject_dict.keys())),classs_copy))
            individual_list=individual_list+classs_copy
        '''

        return individual_list
    ## Must include teacher assignment evaluation, as number of variation of teacher increase, the lower the fitness
    def initialize_teacher_individual(self):
        individual_list = []

        for classs in self.class_instance:
            classs_copy = copy.deepcopy(classs)
            classs_copy = reduce(operator.add, classs_copy.schedule)
            classs_copy = list(
                filter(lambda element: element != "Recess period" and element != "Assembly", classs_copy))

            for period in range(len(classs.subjects)):
                temp_teach = random.choice(list(self.teacher_dict.keys()))
                individual_list.append(temp_teach)

        return individual_list

    def initialize_period_num(self):
        total_period=0

        for classs in self.class_instance:
            classs_copy = copy.deepcopy(classs)
            classs_copy = reduce(operator.add, classs_copy.schedule)
            classs_copy = list(filter(lambda element: element != "Recess period" and element != "Assembly", classs_copy))
            total_period+=len(classs_copy)

        return total_period

    def initialize_period_num_per_class(self):
        total_period = []

        for classs in self.class_instance:
            classs_copy = copy.deepcopy(classs)
            classs_copy = reduce(operator.add, classs_copy.schedule)
            classs_copy = list(
                filter(lambda element: element != "Recess period" and element != "Assembly", classs_copy))
            total_period.append(len(classs_copy))
        return total_period

    def initialize_subject_num_per_class(self):
        subject_number=[]
        for classs in self.class_instance:
            class_sub=[]
            for sub in list(classs.subjects.keys()):
                class_sub.append(next(i for i,j in self.subject_dict.items() if j==sub))
            subject_number.append(class_sub)
        return subject_number

    def initialize_subject_num(self):
        total_subject=0

        for classs in self.class_instance:
            total_subject+=len(classs.subjects)

        return total_subject

    def initialize_schedule_individual(self):
        individual_list = []

        for num,classs in enumerate(self.class_instance):

            '''
            class_subject=list(classs.subjects.keys())
            class_subject=list(filter(lambda x: x[1] in (class_subject), self.subject_dict.items()).keys())
            '''
            for sub in list(classs.subjects.keys()):
                period_remaining = classs.subjects[sub][0]
                while period_remaining>0:
                    individual_list.append(next(k for k,v in self.subject_dict.items() if v == sub))
                    period_remaining-=1

        ##random.shuffle(individual_list)

        return individual_list


    def binary_to_information(self,binary_individual):
        total_period=len(binary_individual[0])

        decoded_array=np.empty((0, 2),int)
        for i in range(int(total_period)):
            subject_num=binary_individual[0][i][:self.subject_bit_length]
            teacher_num=binary_individual[0][i][-self.teacher_bit_length:]

            subject_num=int(subject_num,2)
            teacher_num=int(teacher_num,2)
            ##decoded_array=np.append(decoded_array,[[subject_num,teacher_num]],axis=0)



            decoded_array=np.concatenate((decoded_array, [[subject_num, teacher_num]]), axis=0)


        return decoded_array

    def evaluate_teacher_assignment(self,individual):

        decoded_individual=np.array(individual)

        fitness=0
        individual_counter=0
        class_instance=copy.deepcopy(self.class_instance)
        teacher_instance=copy.deepcopy(self.teacher_instance)
        for classs in class_instance:
            for sub_name, period_remaining in classs.subjects.items():

                teacher_chosen=self.teacher_dict[decoded_individual[individual_counter]]
                teacher_chosen_object=next(i for i in teacher_instance if i.teacher_name == teacher_chosen)

                ##Check for specialty
                if teacher_chosen_object.specialty_subject.subject_name!=sub_name and\
                    next((i.specialty for i in self.subject_instance if i.subject_name == sub_name),False) :

                    fitness-=1
                teacher_chosen_object.assigned_hours+=period_remaining[0]

                        ## increase individual counter
                individual_counter += 1
        for teacher in teacher_instance:
            if teacher.assigned_hours>teacher.max_hours_per_week:
                fitness-=(teacher.assigned_hours-teacher.max_hours_per_week)
        ##self.print_teacher_assigned(individual)
        return [fitness]

    def evaluate_schedule_assignment(self,individual):
        decoded_individual=np.array(individual)

        fitness=0
        individual_counter=0

        wrong_subject_fitness=0
        side_by_side_fitness = 0
        morning_fitness = 0
        Teacher_occupied_fitness = 0
        Subject_remaining_fitness = 0
        max_pd = 0

        class_instance=copy.deepcopy(self.class_instance)
        subject_instance=copy.deepcopy(self.subject_instance)
        teacher_instance=copy.deepcopy(self.teacher_instance)
        teach_instance = copy.deepcopy(self.tach_instance)

        for classs in class_instance:
            for day_num,day in enumerate(classs.schedule):
                side_by_side_fitness_last_day_period=0
                side_by_side_fitness_begin=0
                side_by_side_fitness_middle =0
                side_by_side_fitness_last_period =0
                side_by_side_fitness_else =0


                for period_num,period in enumerate(day):

                    if period!="Recess period" and period!="Assembly":

                        Subject_chosen=self.subject_dict[decoded_individual[individual_counter]]

                        if Subject_chosen not in list(classs.subjects.keys()):
                            Subject_chosen=random.choice(list(classs.subjects.keys()))
                            fitness-=1
                            wrong_subject_fitness -= 1

                        Subject_chosen_object=next(i for i in subject_instance if i.subject_name == Subject_chosen)


                        teacher_chosen = classs.subjects[Subject_chosen][1]
                        teacher_chosen_object = next(i for i in teacher_instance if i.teacher_name == teacher_chosen)

                        teach_instance.append(teach(day=day_num, period=period_num, subject=Subject_chosen,
                                                    teacher_name=teacher_chosen))
                        ## update schedule
                        classs.schedule[day_num][period_num] = teach_instance[-1]

                        ## Decrease fitness if morning class is after recess
                        if Subject_chosen_object.morning_class == True and period_num > classs.Recess_period:
                            fitness -= 1
                            morning_fitness -= 1


                        ## Decrease fitness if class still is supposed to be side by side but do not side by side to full capacity

                        if(Subject_chosen_object.side_by_side == True and classs.subjects[Subject_chosen][0] > 1):
                            if day_num==len(classs.schedule)-1 and period_num==len(classs.schedule[-1])-1:
                                fitness-=1
                                side_by_side_fitness_last_day_period-=1

                                side_by_side_fitness -=1

                            elif isinstance(classs.schedule[day_num][period_num-1],str) or period_num==0:
                                if self.subject_dict[decoded_individual[individual_counter + 1]]!=Subject_chosen:
                                    fitness-=1
                                    side_by_side_fitness_begin -= 1
                                    side_by_side_fitness -= 1

                            elif period_num==(len(day)-1):
                                if classs.schedule[day_num][period_num-1].subject !=Subject_chosen:
                                    fitness-=1
                                    side_by_side_fitness_last_period -= 1
                                    side_by_side_fitness -= 1

                            elif isinstance(classs.schedule[day_num][period_num+1],str):
                                if classs.schedule[day_num][period_num-1].subject !=Subject_chosen:
                                    fitness-=1
                                    side_by_side_fitness_middle -= 1
                                    side_by_side_fitness -= 1
                            else:
                                if classs.schedule[day_num][period_num - 1].subject != Subject_chosen and \
                                    self.subject_dict[decoded_individual[individual_counter + 1]]!=Subject_chosen:
                                        fitness-=1
                                        side_by_side_fitness_else -= 1
                                        side_by_side_fitness -= 1

                                ## Decrease remaining class required for the subject
                        try:
                            classs.subjects[Subject_chosen][0] -= 1
                        except:
                            pass

                        ## increase individual counter
                        individual_counter += 1

                        ## Decrease fitness if teacher is occupied at the time
                        if next((True for lesson in teacher_chosen_object.classes if lesson.day==day_num and lesson.period==period_num ),False):
                            fitness -= 1

                            Teacher_occupied_fitness = 0


                        ## Increase period assigned to teacher
                        teacher_chosen_object.classes.append(teach_instance[-1])


                        ## Decrease fitness if already exceed max hours
                        if teacher_chosen_object.hours_taught() > teacher_chosen_object.assigned_hours:
                            fitness -= 1

                        ## count number of subjects for the day
                my_dict = Counter(i.subject for i in classs.schedule[day_num] if not isinstance(i,str))

                '''
                print("side_by_side_fitness_last_day_period:",side_by_side_fitness_last_day_period)
                print("side_by_side_fitness_begin:",side_by_side_fitness_begin)
                print("side_by_side_fitness_middle:", side_by_side_fitness_middle)
                print("side_by_side_fitness_last_period:",side_by_side_fitness_last_period)
                print("side_by_side_fitness_else:", side_by_side_fitness_else)

                for t in classs.schedule[day_num]:
                    if isinstance(t,str):
                        print(t,end=", ")
                    else:
                        print(t.subject, end=", ")
                print("")
                print(classs.subjects)'''
                    ## Check for maximum number of period of side by side subjects and no side by side subjects
                for teach_activity, total_period in my_dict.items():


                    Subject_object=next(i for i in subject_instance if i.subject_name == teach_activity)

                    if Subject_object.side_by_side == True and total_period > classs.max_sub_pd:

                        fitness -= (total_period - classs.max_sub_pd)
                        max_pd-=(total_period - classs.max_sub_pd)

                    elif Subject_object.side_by_side == False and total_period > 1:
                        fitness -= (total_period - 1)
                        max_pd-=(total_period - 1)

                        ## Decrease fitness according to subject that are supposed to be taught
            fitness -= sum(filter(lambda k:k>=0,map(lambda x: abs(x[0]), list(classs.subjects.values()))))
            Subject_remaining_fitness -= sum(filter(lambda k:k>=0,map(lambda x: abs(x[0]), list(classs.subjects.values()))))
        ##self.print_invididual_to_schedule(individual)
        '''
        print("Wrong subject:",wrong_subject_fitness/fitness,"%",end="  ")
        print("side_by_side_fitness:", side_by_side_fitness / fitness, "%", end="  ")

        print("morning_fitness:", morning_fitness / fitness, "%", end="  ")
        print("Teacher_occupied_fitness:", Teacher_occupied_fitness / fitness, "%", end="  ")
        print("Subject_remaining_fitness:", Subject_remaining_fitness / fitness, "%", end="  ")
        print("max_pd :", max_pd  / fitness, "%")'''

        return [fitness]

    def evaluate(self,individual):

        decoded_individual=np.array([np.array(xi) for xi in individual[0]])

        decoded_individual[:,0]=np.where(decoded_individual[:,0]>=self.subject_total,random.choice(range(self.subject_total)),decoded_individual[:,0])
        decoded_individual[:,1]=np.where(decoded_individual[:,1]>=self.teacher_total,random.choice(range(self.teacher_total)),decoded_individual[:,1])

        fitness=0
        individual_counter=0
        class_instance=copy.deepcopy(self.class_instance)
        subject_instance=copy.deepcopy(self.subject_instance)
        teacher_instance=copy.deepcopy(self.teacher_instance)
        teach_instance = copy.deepcopy(self.tach_instance)


        for classs in self.class_instance:
            teachnum_persubject=dict()
            for day_num,day in enumerate(classs.schedule):

                for period_num,period in enumerate(day):

                    if period!="Recess period" and period!="Assembly":

                        Subject_chosen=self.subject_dict[decoded_individual[:,0][individual_counter]]
                        Subject_chosen_object=next(i for i in subject_instance if i.subject_name == Subject_chosen)

                        teacher_chosen=self.teacher_dict[decoded_individual[:,1][individual_counter]]
                        teacher_chosen_object=next(i for i in teacher_instance if i.teacher_name == teacher_chosen)

                        if Subject_chosen not in teachnum_persubject.keys():
                            teachnum_persubject[Subject_chosen_object]=[teacher_chosen_object]
                        else:
                            if teacher_chosen not in teachnum_persubject[Subject_chosen]:
                                teachnum_persubject[Subject_chosen_object].append(teacher_chosen_object)

                        teach_instance.append(teach(day=day_num, period=period_num, subject=Subject_chosen,
                                                    teacher_name=teacher_chosen))
                        ## update schedule
                        classs.schedule[day_num][period_num] = teach_instance[-1]

                        ## Decrease fitness if morning class is after recess
                        if Subject_chosen_object.morning_class == True and period_num > classs.Recess_period:
                            fitness -= 1

                        ## Decrease fitness if class still is supposed to be side by side but do not side by side to full capacity
                        if Subject_chosen in list(classs.subjects.keys()):
                            '''
                            print(day_num)
                            print(period_num)
                            if (Subject_chosen_object.side_by_side == True and classs.subjects[Subject_chosen][0] > 1) and not isinstance(classs.schedule[day_num][period_num-1],str):
                                if (period_num != len(day) - 1 and period_num != classs.Recess_period - 1) \
                                        and (self.subject_dict[decoded_individual[:,0][individual_counter + 1]] != Subject_chosen
                                             or classs.schedule[day_num][period_num].subject != classs.schedule[day_num][period_num - 1].subject):
                                    fitness -= 1
                                elif (period_num == len(day) - 1 or period_num == classs.Recess_period - 1) and \
                                        classs.schedule[day_num][period_num].subject != classs.schedule[day_num][
                                    period_num - 1].subject:
                                    fitness -= 1
                            '''

                            if(Subject_chosen_object.side_by_side == True and classs.subjects[Subject_chosen][0] > 1):
                                if day_num==len(classs.schedule)-1 and period_num==len(classs.schedule[-1])-1:
                                    fitness-=1
                                elif isinstance(classs.schedule[day_num][period_num-1],str) or period_num==0:
                                    if self.subject_dict[decoded_individual[:,0][individual_counter + 1]]!=Subject_chosen:
                                        fitness-=1
                                elif period_num==(len(day)-1):
                                    if classs.schedule[day_num][period_num-1].subject !=Subject_chosen:
                                        fitness-=1
                                elif isinstance(classs.schedule[day_num][period_num+1],str):
                                    if classs.schedule[day_num][period_num-1].subject !=Subject_chosen:
                                        fitness-=1
                                else:
                                    if classs.schedule[day_num][period_num - 1].subject != Subject_chosen and \
                                        self.subject_dict[decoded_individual[:,0][individual_counter + 1]]!=Subject_chosen:
                                        fitness-=1

                            ## Decrease remaining class required for the subject
                            try:
                                classs.subjects[every_subject][0] -= 1
                            except:
                                pass

                        ## increase individual counter
                        individual_counter += 1


                        ## Decrease fitness if teacher is occupied at the time
                        if next((True for lesson in teacher_chosen_object.classes if lesson.day==day_num and lesson.period==period_num ),False):
                            fitness -= 1

                        ## Increase period assigned to teacher
                        teacher_chosen_object.classes.append(teach_instance[-1])

                        ## Decrease fitness if already exceed max hours

                        if teacher_chosen_object.hours_taught() > teacher_chosen_object.max_hours_per_week:
                            fitness -= 1

                        ## count number of subjects for the day
                my_dict = Counter(classs.schedule[day_num])

                    ## Check for maximum number of period of side by side subjects
                for teach_activity, total_period in my_dict.items():
                    if isinstance(teach_activity, teach):

                        Subject_object=next(i for i in subject_instance if i.subject_name == teach_activity.subject)

                        if Subject_object.side_by_side == True and total_period > classs.max_sub_pd:
                            fitness -= sum(total_period - classs.max_sub_pd)

                    ## Check for maximum number of period of no side by side subjects
                for teach_activity, total_period in my_dict.items():
                    if isinstance(teach_activity, teach):
                        Subject_object=next(i for i in subject_instance if i.subject_name == teach_activity.subject)
                        if Subject_object.side_by_side == False and total_period > 1:
                            fitness -= sum(total_period - classs.max_sub_pd)


                    ## Decrease fitness according to subject that are supposed to be taught
            fitness -= sum(map(lambda x: x[0], list(classs.subjects.values())))

            ## Decrease fitness according to teacher assignment
            ## Number of teacher per subject
            fitness-=sum(len(i) for i in teachnum_persubject.values())-len(teachnum_persubject)
            ## Specialty
            for key,value in teachnum_persubject.items():
                fitness-=len(list(filter(lambda cher:cher.specialty_subject.subject_name!=key.subject_name,value)))


        return [fitness]

    def print_invididual_to_schedule(self,individual):
        individual_counter = 0
        class_instance = copy.deepcopy(self.class_instance)
        subject_instance = copy.deepcopy(self.subject_instance)
        subject_dict=dict(zip(range(len(subject_instance)),subject_instance))
        individual = np.array([np.array(xi) for xi in individual])

        for classs in self.class_instance:

            for day_num, day in enumerate(classs.schedule):
                for period_num, period in enumerate(day):
                    if not isinstance(classs.schedule[day_num][period_num],str):
                        classs.schedule[day_num][period_num] = self.subject_dict[individual[0,individual_counter][0]]
                        individual_counter+=1
                print("{},{}".format(day_num,classs.schedule[day_num]))
            print("")

    def print_teacher_assigned(self,teacher):
        counter=0
        for classs in self.class_instance:
            print(classs.class_name)
            for sub_name in list(classs.subjects.keys()):
                print(sub_name," : ",self.teacher_dict[teacher[counter]],end="   ")
                counter+=1

    def mutation(self,individual,indpb):

        ##decoded_individual=np.array([np.array(xi) for xi in individual[0]])
        for i in range(2):
            if random.random() < indpb:
                ##random_period=random.choice(range(len(individual)))
                class_choice=random.choice(range(len(self.class_instance)))
                period_choice=random.choice(range(self.period_number_list[class_choice]))
                individual[sum(self.period_number_list[:class_choice])+period_choice]=random.choice(self.subject_number_list[class_choice])
                ##random_period_2=random.choice(range(len(individual)))

                ##individual[random_period_2] = random.choice(range(self.teacher_total))
                ##individual[random_period][0]=random.choice(range(self.subject_total))
                ##individual[random_period_2][1]=random.choice(range(self.teacher_total))
                
                ##decoded_individual[random_period][0]=random.choice(range(self.subject_total))
                ##decoded_individual[random_period][1]=random.choice(range(self.teacher_total))
                
            ##decoded_individual=np.expand_dims(decoded_individual, axis=0).tolist()


        return individual ,

    def random_teacher_list(self):
        return random.choice(list(self.teacher_dict.keys()))

    def random_subject_list(self):
        return random.choice(list(self.subject_dict.keys()))

    def assign_teacher(self,solution):
        counter=0
        for classs in self.class_instance:
            for subject in list(classs.subjects.keys()):
                classs.subjects[subject].append(self.teacher_dict[solution[counter]])
                teacher=next(teacher for teacher in self.teacher_instance if self.teacher_dict[solution[counter]]==teacher.teacher_name)
                teacher.assigned_hours+=classs.subjects[subject][0]
                counter+=1


    def main(self):
        '''
        NB_QUEENS=50
        creator.create("FitnessMax",base.Fitness,weights=(1.0,))
        creator.create("Individual",list,fitness=creator.FitnessMax)
        print(self.initialize_period_num())
        toolbox=base.Toolbox()
        ##toolbox.register("permutation", random.sample, range(NB_QUEENS), NB_QUEENS)
        ##toolbox.register("individual",tools.initRepeat,creator.Individual,self.initialize_individual,n=1)
        toolbox.register("individual", tools.initRepeat, creator.Individual,self.random_teacher_list , n=int(self.initialize_subject_num()))
        toolbox.register("population",tools.initRepeat,list,toolbox.individual)
        ##toolbox.register("evaluate",self.evaluate)
        toolbox.register("evaluate", self.evaluate_teacher_assignment)
        ##toolbox.register("mate", tools.cxPartialyMatched)
        toolbox.register("mate",tools.cxUniform,indpb=0.7)
        ##toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate",self.mutation,indpb=0.6)
        ##toolbox.register("mutate", tools.mutUniformInt, low=0,up=len(self.teacher_dict)-1,indpb=0.8)
        toolbox.register("select", tools.selRoulette)
        ##toolbox.register("select",tools.selTournament,tournsize=200)

        pop=toolbox.population(n=300)

        HALLOFFAME=tools.HallOfFame(1)

        stats = tools.Statistics(key=lambda ind: ind.fitness.values)

        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)


        pop,logbook=algorithms.eaSimple(pop, toolbox, cxpb=1, mutpb=1, ngen=100,
                            stats=stats, halloffame=HALLOFFAME,verbose=True)
        solution=next(indiv for indiv in pop if self.evaluate_teacher_assignment(indiv)[0]==0)
        self.print_teacher_assigned(solution)
        print(solution)
        '''
        self.assign_teacher([7, 6, 11, 10, 9, 3, 1, 0, 5, 8, 0, 7, 8, 11, 10, 9, 3, 1, 5, 4, 5, 2])
        for teacher in self.teacher_instance:
            print(teacher.teacher_name,":",teacher.assigned_hours)

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        toolbox = base.Toolbox()
        ##toolbox.register("permutation", random.sample, range(NB_QUEENS), NB_QUEENS)
        ##toolbox.register("individual",tools.initRepeat,creator.Individual,self.initialize_individual,n=1)
        ##toolbox.register("individual", tools.initRepeat, creator.Individual, self.random_subject_list,
        toolbox.register("individual", tools.initIterate, creator.Individual, self.initialize_schedule_individual)

        toolbox.register("population", tools.initRepeat, list, toolbox.individual,n=300)
        toolbox.register("populations", tools.initRepeat, list, toolbox.population)

        ##toolbox.register("evaluate",self.evaluate)
        toolbox.register("evaluate", self.evaluate_schedule_assignment)
        ##toolbox.register("mate", tools.cxPartialyMatched)
        ##toolbox.register("mate", tools.cxOrdered)
        ##toolbox.register("mate", tools.cxPartialyMatched)
        toolbox.register("mate", tools.cxOrdered_by_class,period_number_list=self.period_number_list)


        ##toolbox.register("mate", tools.cxUniform, indpb=0.5)
        ##toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", self.mutation, indpb=0.2)
        ##toolbox.register("mutate", tools.mutUniformInt, low=0,up=len(self.teacher_dict)-1,indpb=0.8)
        ##toolbox.register("select", tools.selRoulette)
        toolbox.register("migrate", tools.migRing, k=30, selection=tools.selRandom,
                         replacement=tools.selRandom)
        toolbox.register("select",tools.selTournament,tournsize=10)
        ##toolbox.register("select", tools.selAutomaticEpsilonLexicase)

        ##pop = toolbox.population(n=300)
        pops=toolbox.populations(n=3)

        HALLOFFAME = tools.HallOfFame(1)

        stats = tools.Statistics(key=lambda ind: ind.fitness.values)

        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)

        pop, logbook = algorithms.eaSimple(pops, toolbox, cxpb=0.3, mutpb=0.5, ngen=1000,
                                           stats=stats, halloffame=HALLOFFAME, verbose=True)
        '''
        fitnesses=list(map(toolbox.evaluate,pop))

        for ind,fit in zip(pop,fitnesses):
            ind.fitness.values=fit

        CXPB,MUTPB=1,1

        fits=[ind.fitness.values[0] for ind in pop]

        g=0
        
        while g<500:

            g=g+1

            offspring=toolbox.select(pop,len(pop))

            offspring=list(map(toolbox.clone,offspring))

            for child1,child2 in zip(offspring[::2],offspring[1::2]):
                if random.random()<CXPB:
                    toolbox.mate(child1,child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random()<MUTPB:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values

            invalid_ind=[ind for ind in offspring if not ind.fitness.valid]
            fitnesses=map(toolbox.evaluate,invalid_ind)
            for ind,fit in zip(invalid_ind,fitnesses):
                ind.fitness.values=fit

            pop[:]=offspring
           '''

        solution = next(indiv for indiv in pop if self.evaluate_schedule_assignment(indiv)[0] == 0)
        self.print_invididual_to_schedule(solution)



'''
                        teacher_name=classs.subjects[Subject_chosen][1]

                        teach_instance.append(teach(day=day_num, period=period_num, subject=Subject_chosen,
                                                    teacher_name=teacher_name))
                        ## update schedule
                        classs.schedule[day_num][period_num]=teach_instance[-1]

                        ## Decrease fitness if morning class is after recess
                        if Subject_chosen.morning_class==True and period_num>classs.Recess_period:
                            fitness-=1
                        ##print(classs.schedule[day_num][period_num].subject.subject_name)
                        ## Decrease fitness if class still is supposed to be side by side but do not side by side to full capacity
                        if Subject_chosen.side_by_side==True and classs.subjects[Subject_chosen][0]>1:
                            if (period_num!=len(day)-1 and period_num!=classs.Recess_period-1)\
                                    and (subject_dict[individual[0][individual_counter+1]]!=Subject_chosen
                                        or classs.schedule[day_num][period_num].subject!=classs.schedule[day_num][period_num-1].subject):
                                fitness-=1
                            elif (period_num==len(day)-1 or period_num==classs.Recess_period-1) and classs.schedule[day_num][period_num].subject!=classs.schedule[day_num][period_num-1].subject:
                                fitness-=1

                        ## Decrease remaining class required for the subject
                        try:
                            classs.subjects[every_subject][0]-=1
                        except:
                            pass

                        ## increase individual counter
                        individual_counter+=1

                        classs.subjects[Subject_chosen][1].classes.append(teach_instance[-1])

                        ## Decrease fitness if teacher is occupied at the time
                        if [day_num,period_num] in classs.subjects[Subject_chosen][1].teach_schedule():
                            fitness-=1

                        ## Increase period assigned to teacher
                        classs.subjects[Subject_chosen][1].classes.append(teach_instance[-1])

                        ##
                        print(classs.subjects[Subject_chosen][1].assigned_hours())
                        if classs.subjects[Subject_chosen][1].assigned_hours()>classs.subjects[Subject_chosen].max_hours_per_week:
                            fitness-=1

                ## count number of subjects for the day
                my_dict = {i: MyList.count(i) for i in classs.schedule[day] if isinstance(i,Subject)}

                ## Check for maximum number of period of side by side subjects
                fitness-=sum([total_period-classs.max_sub_pd for subject,total_period in my_dict.items() if subject.side_by_side==True and total_period>classs.max_sub_pd])

                ## Check for maximum number of period of no side by side subjects
                fitness-=sum([total_period-1 for subject,total_period in my_dict.items() if subject.side_by_side==False and total_period>1])

            ## Decrease fitness according to subject that are supposed to be taught
            fitness-=sum(map(lambda x:x[0],list(classs.subjects.values())))

        return fitness
'''