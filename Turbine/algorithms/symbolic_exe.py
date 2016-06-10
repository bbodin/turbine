import logging
import time


class SymbolicExe:
    def __init__(self, dataflow):
        self.dataflow = dataflow
        self.start_time = {}
        self.time_tick = 0
        self.currently_executed = []
        self.tick_left = {}

    def get_start_time(self, nb_ite=1):
        return self.execute(get_start_time=True, nb_ite=nb_ite)

    # Execute the symbolic execution until the number of iteration reach self.ite
    def execute(self, get_start_time=False, nb_ite=1):
        self.__raz()
        # start time of tasks/phase : (key = task, [start_time1, start_time2,...]) for SDF
        #                             (key = (task, phase), [start_time1, start_time2,...]) for CSDF or PCG
        num_task_exe = [0] * self.dataflow.get_task_count()  # execution number of the task during current step
        executed_task = [False] * self.dataflow.get_task_count()  # if the task can be executed
        debut = time.time()
        terminate = False  # Symbolic exe succeed ?
        step_two = False  # Engage step Two ?
        i = 0
        for task in self.dataflow.get_task_list():
            num_task_exe[task] = 0
        # ~ print "PHASE ONE"
        while not terminate:
            for task in self.dataflow.get_task_list():  # zero executed task
                executed_task[task] = False
            # 1 - Choose which task can be execute
            task_execute = len(self.currently_executed)
            logging.debug("iteration: " + str(i))
            for task in self.dataflow.get_task_list():
                if task not in self.currently_executed and self.__is_executable(task):
                    executed_task[task] = True

                    # If we are in step Two
                    if self.dataflow.is_sdf:
                        phase_count = 1
                    else:
                        phase_count = float(self.dataflow.get_phase_count(task))

                    rep_fact = float(self.dataflow.get_repetition_factor(task))
                    if step_two and float(num_task_exe[task]) / phase_count == rep_fact*nb_ite:
                        # If the task has been executed enought then don't execute it
                        executed_task[task] = False
                        task_execute -= 1
                    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                        logging.debug("execute task: " + str(task))
                        for arc in self.dataflow.get_arc_list(target=task):
                            logging.debug("\tInput arc: " + str(arc) + " M0=" + str(self.M0[arc]))
                    task_execute += 1
            # 2 - Execute tasks selected
            for task in self.dataflow.get_task_list():
                if executed_task[task]:  # If the task is selected
                    if get_start_time:
                        if self.dataflow.is_sdf:
                            self.start_time[task].append(self.time_tick)
                        if self.dataflow.is_csdf:
                            self.start_time[(task, self.currentPhase[task])].append(self.time_tick)
                    num_task_exe[task] += 1  # Increase the number of exe of this task
                    if self.__task_start_exe(task) == -1:  # If the execution went wrong stop the process
                        logging.error("Negative bds, this should never occur...")
                        return -1
                    self.currently_executed.append(task)
                    self.tick_left[task] = self.__get_duration(task)

            increment = min(self.tick_left.items(), key=lambda x: x[1])[1]
            del_temp = []
            for task in self.currently_executed:
                self.tick_left[task] -= increment
                if self.tick_left[task] == 0:
                    self.__task_end_exe(task)
                    del_temp.append(task)
            for task in del_temp:
                del self.tick_left[task]
                self.currently_executed.remove(task)
            self.time_tick += increment

            # Should we go to step Two ?
            if not step_two:
                num_exe = 0  # Number of task which has enough execution
                for task in self.dataflow.get_task_list():
                    if self.dataflow.is_sdf:
                        max_exe = 1
                    if self.dataflow.is_csdf:
                        max_exe = self.dataflow.get_phase_count(task)
                    if self.dataflow.is_pcg:
                        max_exe += self.dataflow.get_ini_phase_count(task)
                    if num_task_exe[task] >= max_exe:
                        num_exe += 1
                if num_exe == self.dataflow.get_task_count():
                    logging.debug("number of exe: " + str(num_task_exe))
                    for task in self.dataflow.get_task_list():
                        num_task_exe[task] = 0
                    step_two = True
                    logging.debug("PHASE TWO ENGAGE !!! fasten your seatbelt.")

            # Step Two over ?
            if step_two:
                num_exe = 0  # Number of task which has enought execution
                for task in self.dataflow.get_task_list():
                    # If the number of execution of the task is more or equal to its repetition factor
                    if self.dataflow.is_sdf:
                        phase_count = 1.0
                    else:
                        phase_count = float(self.dataflow.get_phase_count(task))
                    rep_fact = float(self.dataflow.get_repetition_factor(task))
                    if float(num_task_exe[task]) / phase_count == rep_fact * nb_ite:
                        num_exe += 1
                # If all task have been executed enought the symbolic exe is successful
                if num_exe == self.dataflow.get_task_count():
                    terminate = True

            # If nothing append the initial marking is wrong:-(
            if task_execute == 0:
                logging.info("No task executed:-/, iteration: " + str(i))
                logging.info("Arcs exe: " + str(self.arcExe))
                logging.debug("number of exe: " + str(num_task_exe))
                return -1
            i += 1
        fin = time.time()
        logging.info("Symbolic execution succeed in " + str(fin - debut) + "s, with " + str(i) + " iterations")
        if get_start_time:
            return self.start_time
        return 0  # Exe successful

    # Used when __init__ is called
    # Initialized preload and phases
    # Phases are negative when the graph have initialized phases.
    def __raz(self):
        self.arcExe = 0
        self.time_tick = 0
        self.currently_executed = []
        self.tick_left = {}

        self.M0 = {}
        for arc in self.dataflow.get_arc_list():
            self.M0[arc] = self.dataflow.get_initial_marking(arc)

        self.currentPhase = {}
        for task in self.dataflow.get_task_list():
            self.currentPhase[task] = 0
            if self.dataflow.is_sdf:
                self.start_time[task] = []
            if self.dataflow.is_csdf:
                for phase in xrange(self.dataflow.get_phase_count(task)):
                    self.start_time[(task, phase)] = []
            if self.dataflow.is_pcg:
                self.currentPhase[task] = -self.dataflow.get_ini_phase_count(task)

    # Start the execution of a task: delete preload from input arcs
    def __task_start_exe(self, task):
        for inArc in self.dataflow.get_arc_list(target=task):
            self.M0[inArc] -= self.__get_token_del(inArc)
            if self.M0[inArc] < 0:
                return -1
            self.arcExe += 1
        return 0

    # End the execution of a task: add preload on output arc
    # and increment the actual phase of the task
    def __task_end_exe(self, task):
        for outArc in self.dataflow.get_arc_list(source=task):
            self.M0[outArc] += self.__get_token_created(outArc)
            self.arcExe += 1

        self.currentPhase[task] += 1
        if self.dataflow.is_sdf:
            self.currentPhase[task] = 0
        else:
            if self.currentPhase[task] == self.dataflow.get_phase_count(task):
                self.currentPhase[task] = 0

        return 0

    # Return True if the task is executable (ie input arcs have enough initial marking)
    def __is_executable(self, task):
        for inArc in self.dataflow.get_arc_list(target=task):
            if self.M0[inArc] < self.__get_token_need(inArc):
                return False
        return True

    # Return the amount of data create on an arc depending of his production and the actual phase of the source
    def __get_token_created(self, out_arc):
        task = self.dataflow.get_source(out_arc)
        cur_phase = self.currentPhase[task]
        if cur_phase < 0:
            return self.dataflow.get_ini_prod_rate_list(out_arc)[self.dataflow.get_ini_phase_count(task) + cur_phase]
        else:
            if self.dataflow.is_sdf:
                return self.dataflow.get_prod_rate(out_arc)
            else:
                return self.dataflow.get_prod_rate_list(out_arc)[cur_phase]

    # Return the amount of data del on an input arc when the target is execute.
    def __get_token_del(self, in_arc):
        task = self.dataflow.get_target(in_arc)
        cur_phase = self.currentPhase[task]

        if cur_phase < 0:
            return self.dataflow.get_ini_cons_rate_list(in_arc)[self.dataflow.get_ini_phase_count(task) + cur_phase]
        else:
            if self.dataflow.is_sdf:
                return self.dataflow.get_cons_rate(in_arc)
            else:
                return self.dataflow.get_cons_rate_list(in_arc)[cur_phase]

    # return the data needed by an arc to execute the current phase of the target.
    def __get_token_need(self, in_arc):
        task = self.dataflow.get_target(in_arc)
        cur_phase = self.currentPhase[task]

        if self.dataflow.is_pcg:
            if cur_phase < 0:
                data_need = self.dataflow.get_ini_threshold_list(in_arc)[
                    self.dataflow.get_ini_phase_count(task) + cur_phase]
            else:
                data_need = self.dataflow.get_threshold_list(in_arc)[cur_phase]
        else:
            return self.__get_token_del(in_arc)
        return data_need

    # def __get_start_time(self, task):
    #     t_start_time = 0
    #     if len(self.start_time[task]) != 0:
    #         t_start_time = max(self.start_time[task]) + self.__get_duration(task)
    #     for arc in self.dataflow.get_arc_list(target=task):
    #         source = self.dataflow.get_source(arc)
    #         if self.M0[arc] - self.__get_token_created(arc) < self.__get_token_need(arc):
    #             if len(self.start_time[source]) != 0:
    #                 t_start_time = max(t_start_time, max(self.start_time[source]) + self.__get_duration(source))
    #     return t_start_time

    def __get_duration(self, task):
        if self.dataflow.is_sdf:
            return self.dataflow.get_task_duration(task)
        if self.dataflow.is_pcg and self.currentPhase[task] < 0:
            phase = self.dataflow.get_ini_phase_count(task) + self.currentPhase[task]
            return self.dataflow.get_ini_phase_duration_list(task)[phase]
        if self.dataflow.is_csdf:
            return self.dataflow.get_phase_duration_list(task)[self.currentPhase[task]]

    ########################################################################
    #                       Printing fonctions                             #
    ########################################################################
    # Print the actual amount of each bds (arcs)
    def print_buffer(self):
        for arc in self.dataflow.get_arc_list():
            print str(arc) + " M0: " + str(self.M0[arc])
        print "------------------------------"

    # Print all arc which are blocking the graph. If all task are impacted, the graph is not alive.
    def print_blocking_task(self):
        for task in self.dataflow.get_task_list():
            if not self.__is_executable(task):
                for inArc in self.dataflow.get_arc_list(target=task):
                    if self.M0[inArc] < self.__get_token_need(inArc):
                        print "BLOCKING ARC: " + str(inArc) + " phase: " + str(self.currentPhase[task]) + " need: " \
                              + str(self.__get_token_need(inArc)) + " bds: " + str(self.M0[inArc]) + " STEP: " \
                              + str(self.dataflow.get_gcd(inArc))

    # Print all task that can be executed. If None, the graph is not alive.
    def print_no_blocking_task(self):
        for task in self.dataflow.get_task_list():
            for inArc in self.dataflow.get_arc_list(target=task):
                if self.M0[inArc] > self.__get_token_need(inArc):
                    print "NO BLOCKING ARC: " + str(inArc) + " phase: " + str(self.currentPhase[task]) + " need: " \
                          + str(self.__get_token_need(inArc)) + " bds: " + str(self.M0[inArc]) + " STEP: " \
                          + str(self.dataflow.get_gcd(inArc))
