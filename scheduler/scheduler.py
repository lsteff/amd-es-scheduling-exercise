from dataclasses import dataclass
import copy

import matplotlib.pyplot as plt
import seaborn

seaborn.set_theme(context="notebook", style="darkgrid")

plt.rcParams["figure.figsize"] = [12, 8]


@dataclass
class Task:
    id: int
    duration: int
    release: int
    priority: int = None
    deadline: int = None


@dataclass
class Schedule:
    tasks: list[Task]
    time_slices: list[int]

    def to_dict(self):
        new_schedule = dict()
        for t in self.tasks:
            new_schedule[t.id] = list()

        # step through time, whenever the active tasks changes, we add a new segment
        current_id = self.time_slices[0]
        segment_start = 0
        for t, id in enumerate(self.time_slices):
            if id != current_id:  # a new segment starts
                if current_id is not None:
                    new_schedule[current_id].append((segment_start, t))
                current_id = id
                segment_start = t
        return new_schedule

    def gantt_chart(self):
        # We use matplotlibs barh-chart for bulding a gantt-chart.
        # That means we need to pass the "blocks" as three arrays
        # y, width and left
        y = []
        width = []
        left = []

        sched_dict = self.to_dict()

        unique_ids = set()
        for task_id, time_slices in sched_dict.items():
            unique_ids.add(task_id)
            for start, end in time_slices:
                y.append(task_id)
                left.append(start)
                width.append(end - start)

        unique_ids = sorted(unique_ids)

        assert len(y) == len(width)
        assert len(y) == len(left)
        assert len(width) == len(left)

        labels = [f"$v_{i}$" for i in unique_ids]

        plt.barh(y=y, width=width, left=left, height=0.4)
        plt.yticks(ticks=unique_ids, labels=labels)
        plt.xlim((0, None))

        # add deadlines (if present)
        v_x = []
        v_ymin = []
        v_ymax = []
        for t in self.tasks:
            if t.deadline is not None:
                # dirty: we use the id of the task as its y_pos
                v_x.append(t.deadline)
                pos = t.id
                v_ymin.append(pos - 0.4)
                v_ymax.append(pos + 0.4)
        plt.vlines(x=v_x, ymin=v_ymin, ymax=v_ymax, colors="red", linewidth=2.0)

        # do the same for release times
        v_x = []
        v_ymin = []
        v_ymax = []
        for t in self.tasks:
            if t.release is not None:
                # dirty: we use the id of the task as its y_pos
                v_x.append(t.release)
                pos = t.id
                v_ymin.append(pos - 0.4)
                v_ymax.append(pos + 0.4)
        plt.vlines(x=v_x, ymin=v_ymin, ymax=v_ymax, colors="green", linewidth=2.0)

        plt.show()


class Scheduler:
    def __init__(self) -> None:
        self.current_task: Task = None
        self.tasks_active = []
        self._current_time: int = 0

    # gets called every "cycle"
    def update(self, new_tasks):
        raise NotImplementedError()

    def schedule(self, tasks_to_schedule) -> Schedule:
        self.current_task = None
        self._current_time = 0  # this should not be set to 1, as the tasks in the tasklist at time 0 will otherwise never be scheduled and we have an infinite loop

        task_list = tasks_to_schedule.copy()
        schedule = Schedule(tasks=tasks_to_schedule.copy(), time_slices=list())

        # a schedule is just a list of task id's
        # so that "schedule[5] == 42" means that task 42 ran on the fifth cycle
        # schedule = []
        time_step = 1

        # last check is kind of a hack, since the tasks_pending list starts as empty
        # also, will not work if there is no task with a release time of 0
        while len(task_list) > 0 or len(self.tasks_active) > 0:
            if self.current_task:
                self.current_task.duration -= time_step

                if self.current_task.duration <= 0:
                    self.tasks_active.remove(self.current_task)
                    self.current_task = None

            # find every task from task_list that releases at the current time and remove it
            new_tasks = []
            for task in task_list[:]:  # [:] creates a shallow copy of the list
                if self._current_time == task.release:
                    new_tasks.append(copy.deepcopy(task))
                    task_list.remove(task)

            self.update(new_tasks)

            # we may append "None", but that signifies no task ran at the current time
            if self.current_task is None:
                schedule.time_slices.append(None)
            else:
                schedule.time_slices.append(self.current_task.id)

            self._current_time += time_step

        # to make working with the schedule easier, we convert it to a dictionary
        # return to_dict(schedule)
        return schedule