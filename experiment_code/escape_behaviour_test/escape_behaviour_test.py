#  -*- coding: utf-8 -*-
import pickle

from psychopy import visual, core, event, gui
import ConfigParser
import logging
import random
import sys
from random import uniform
from io import open
import os

import numpy as np
import pygame

from utils.shock_handler import Shocker, Empty_Shocker
from utils.audio_handler import Audio, EmptyAudio
from utils.dialog_box import DialogBox

CONFIG_PATH = "escape_behaviour_test/configs/default_config"

def ConfigSectionMap(Config, section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option.upper()] = Config.get(section, option)
            if dict1[option.upper()] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option.upper()] = None
    return dict1


class Priority_Dict:
    def __init__(self, path):
        self.conf = ConfigParser.ConfigParser()
        with open(path, 'r', encoding='utf-8') as f:
            self.conf.readfp(f)
        # self.conf.read(path)
        self.priority = [self.get_dict("EBT")]

    def set_phase(self, num):
        self.priority = [self.get_dict("PHASE%s" % num), self.get_dict("EBT")]

    def __getitem__(self, item):
        for p in self.priority:
            if item in p:
                return p[item]

    def get_dict(self, section):
        dict1 = {}
        options = self.conf.options(section)
        for option in options:
            try:
                dict1[option.upper()] = self.conf.get(section, option)
                if dict1[option.upper()] == -1:
                    print("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                dict1[option.upper()] = None
        return dict1


class CSV_Writer:
    """Only works if file is not deleted while program is running
    In this case however our data is corrupted either way.
    I hope nobody does this for whatever reason"""

    def __init__(self, path, titles):
        import errno

        self.path = path
        if not os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        self.write_line(titles)

    def write_line(self, values):
        with open(self.path, "a") as f:
            l = ",".join([str(val) for val in values])
            l = l + '\n'
            f.write(unicode(l))


class Pause_Screen:
    def __init__(self, config):
        self.config = config
        self.x_size = int(self.config["X_SIZE"])
        self.y_size = int(self.config["Y_SIZE"])
        self.text_size = int(self.config["TEXT_SIZE"])
        self.text = self.config["TEXT"].split('<br>')

        self.timeout = int(self.config["TIMEOUT"])
        self.break_on_key = self.config["BREAK_ON_KEY"]
        os.environ['SDL_VIDEO_CENTERED'] = '1'

    def show(self):
        pygame.init()
        # Fixes resolution bug, but causes flicker
        #pygame.display.quit()
        #pygame.display.init()
        if self.config["FULL_SCREEN"] == "TRUE":
            self.screen = pygame.display.set_mode([0, 0], pygame.FULLSCREEN)
            self.x_size = self.screen.get_width()
            self.y_size = self.screen.get_height()
        else:
            self.screen = pygame.display.set_mode((self.x_size, self.y_size), pygame.NOFRAME)
        self.font = pygame.font.SysFont("arial", int(self.text_size))

        # render text
        labels = [self.font.render(t, 1, (255, 255, 255)) for t in self.text]

        # for label in labels:
        #    word_width, word_height = word_surface.get_size()
        # label_rects = [label.get_rect(center=(self.x_size/2,self.y_size/2)) for label in labels]
        stop = False
        height = max([l.get_size()[1] for l in labels])
        timeout = core.CountdownTimer(int(self.timeout))

        while not stop and timeout.getTime() > 0:
            self.screen.fill((0, 0, 0))
            for ind, label in enumerate(labels):
                label_rect = label.get_rect(center=(self.x_size / 2, self.y_size / 2 - (len(labels) / 2 - ind) * height))
                self.screen.blit(label, label_rect)
            pygame.display.update()

            if self.break_on_key == "TRUE":
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        stop = True


                        # pygame.quit()

class Map:
    EMPTY = 0
    WALL = 1
    START = 2
    SAFE = 3  # is this even used?
    GOAL = 4

    CHAR_MAP = {'#': EMPTY, 'W': WALL, 'A': START, 'G': GOAL}

    def __init__(self, map_config):
        self._map_config = map_config

        # Visual properties from MAP_CONFIG section
        self.tile_size = int(self._map_config["TILE_SIZE"])
        self.margin = int(self._map_config["TILE_MARGIN"])
        self.background_color = pygame.Color(*[int(i) for i in self._map_config["BACKGROUND_COLOR"].split(",")])
        self.special_color_map = {self.WALL: pygame.Color(*[int(i) for i in self._map_config["WALL_COLOR"].split(",")]),
                                  self.EMPTY: pygame.Color(*[int(i) for i in self._map_config["TILE_COLOR"].split(",")]),
                                  self.GOAL: pygame.Color(*[int(i) for i in self._map_config["GOAL_COLOR"].split(",")])}

        # Logical properties, set by load or random
        self.num_tiles_x = None
        self.num_tiles_y = None
        self.field = None
        self.goals = None
        self.start_pos = None

    @classmethod
    def load(cls, map_config):
        """
        Loads a map from file
        :param map_config: MAP_CONFIG section of config
        :param path: to map file
        :return: Map object
        """

        map_ = Map(map_config=map_config)
        path = map_config['MAP']
        lines = []
        try:
            f = open(path, "r")
        except IOError:
            script_dir = os.path.dirname(__file__)
            f = open(os.path.join(script_dir, path))

        lines = f.read().splitlines()

        f.close()

        map_.num_tiles_y = len(lines)
        map_.num_tiles_x = len(lines[0])
        map_.field = np.zeros((map_.num_tiles_x, map_.num_tiles_y))
        # stored map is translated into columns and rows with the numbers specified before (EMPTY=0, GOAL=4 etc.)
        map_.goals = []
        for i in range(map_.num_tiles_x):
            for j in range(map_.num_tiles_y):
                map_.field[i, j] = cls.CHAR_MAP[lines[j][i]]
                if map_.field[i, j] == map_.GOAL:
                    map_.goals.append((i,j))
                elif map_.field[i, j] == map_.START:
                    map_.start_pos = [i, j]
        return map_

    @classmethod
    def random(cls, map_config, random_map_config):
        """
        Generate randomized map
        :param map_config: MAP_CONFIG section of config
        :param random_map_config: RANDOM section of config
        :return: Map object
        """
        map_ = Map(map_config=map_config)

        map_.num_tiles_x = int(random_map_config["X_SIZE"])
        map_.num_tiles_y = int(random_map_config["Y_SIZE"])
        map_.field = np.zeros((map_.num_tiles_x, map_.num_tiles_y))
        num_goals = int(random_map_config["NUM_GOALS"])

        # Init start
        if random_map_config["START_POS"] == "RANDOM":
            map_.start_pos = [random.randint(0, map_.num_tiles_x - 1), random.randint(0, map_.num_tiles_y - 1)]
        else:
            map_.start_pos = [int(i) for i in random_map_config["START_POS"].split(",")]
        map_.field[map_.start_pos[0], map_.start_pos[1]] = map_.START

        # Generate goals
        map_.goals = []
        for _ in range(num_goals):
            goal = map_.start_pos
            while ((map_.start_pos[0] - 1 <= goal[0] <= map_.start_pos[0] + 1 and
                    map_.start_pos[1] - 1 <= goal[1] <= map_.start_pos[1] + 1) or
                    goal in map_.goals):
                goal = (random.randint(0, map_.num_tiles_x - 1), random.randint(0, map_.num_tiles_y - 1))
            # Add goal to list of goals
            map_.goals.append(goal)
            # Set goal on field
            map_.field[goal[0], goal[1]] = map_.GOAL
        return map_

    @classmethod
    def empty(cls, map_config, exploration_map_config):
        """
        Builds empty map with fake goals.
        The field will contain no goals. Goals are all (-1,-1),
        :param map_config: MAP_CONFIG section of config
        :param exploration_map_config: EXPLORATION_MAP section of config
        :return: Map object
        """
        map_ = Map(map_config=map_config)
        map_.num_tiles_x = int(exploration_map_config["X_SIZE"])
        map_.num_tiles_y = int(exploration_map_config["Y_SIZE"])
        map_.field = np.zeros((map_.num_tiles_x, map_.num_tiles_y))

        # Init start
        if exploration_map_config["START_POS"] == "RANDOM":
            map_.start_pos = [random.randint(0, map_.num_tiles_x - 1), random.randint(0, map_.num_tiles_y - 1)]
        else:
            map_.start_pos = [int(i) for i in exploration_map_config["START_POS"].split(",")]
        map_.field[map_.start_pos[0], map_.start_pos[1]] = map_.START

        # Goals
        map_.goals = [(-1,-1)] * int(exploration_map_config["NUM_GOALS"])

        return map_

class EscapeBehaviourTest:


    def __init__(self, config,block_number=1, trial_number=1, phase_number=1, subject_ID="NA", condition="NA", start_time="NA"):

        pygame.mixer.pre_init(44100, -16, 2, 512)
        self.log = logging.getLogger("EBT")
        self.csv_writer = None
        self.csv_writer_phaseDur = None
        self.log.setLevel(logging.DEBUG)
        self.START_TIME = start_time
        self.config = config
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.block_number = block_number
        self.trial_number = trial_number
        self.phase_number = phase_number
        self.name = self.config["NAME"]
        self.subject_ID = subject_ID
        self.condition = condition
        self._map = Map(self.config.get_dict("MAP_CONFIG"))
        self.init_map()
        self.init_saver()
        self.init_stress()
        self.init_game()

    def reload(self, block_number, trial_number, phase_number, config=None, map_=None):
        self.block_number = block_number
        self.trial_number = trial_number
        self.phase_number = phase_number
        if config != None:
            self.config = config

        pygame.init()
        if map_ is not None:
            self.init_map(map_)
        self.init_saver()
        self.init_stress()
        self.init_game()

    def init_map(self, _map=None):
        if _map is not None:
            self._map = _map
        else:
            map_config = self.config.get_dict("MAP_CONFIG")
            if map_config['MAP'] == "RANDOM":
                self._map = Map.random(map_config, self.config.get_dict("RANDOM"))
            else:
                self._map = Map.load(map_config)

    def init_saver(self):
        self.name = self.config["NAME"]
        # POSSIB = ["trial_number","phase_number"]

        self.save_dict = self.config.get_dict("SAVE_CONFIGURATION")

        script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

        save_path = os.path.join(script_dir + "/output", self.subject_ID + "_" + self.START_TIME)

        self.save_vals = ["subject_ID", "condition", "block", "trial", "phase", "name", "x", "y", "goal", "move", "rt"]
        self.save_con = self.save_dict["SAVE_CONDITION"]

        # Add columns for goal positions
        for i in range(1, len(self._map.goals) + 1):
            self.save_vals.append("SP_" + str(i) + "x")
            self.save_vals.append("SP_" + str(i) + "y")

        if self.csv_writer == None:
            self.csv_writer = CSV_Writer(save_path + ".csv", self.save_vals)

        if self.csv_writer_phaseDur == None:
            self.csv_writer_phaseDur = CSV_Writer(save_path + '_phaseduration' + ".csv", ['block','trial', 'phase', 'duration'])

    def init_stress(self):
        self.ISI_MIN = float(self.config["ISI_MIN"])
        self.ISI_MAX = float(self.config["ISI_MAX"])
        self.sound_time = float(self.config["SOUND_LENGTH"])

        # NUMBER_OF_SHOCK_REPETITIONS:2

        # At multiples of x ms a shock will be administered (+/- Jitter)
        self.num_shocks = int(self.config["MAX_SHOCKS_PER_PHASE"])
        self.shock_base_time = int(self.config["SHOCK_EVERY"])
        self.jitter = int(self.config["JITTER"])

        self.shock_times = [(i + 1) * self.shock_base_time + random.randint(-self.jitter, self.jitter) for i in
                            range(self.num_shocks)]
        self.shock_times = [float(v) / 1000 for v in self.shock_times]
        self.current_shock = 0

        self.num_shocks = int(self.config["MAX_SHOCKS_PER_PHASE"])
        # self.time_between_shocks = float(self.config["TIME_BETWEEN_SHOCKS"])
        if self.config["NOISE"] == "TRUE":
            self.shock_sound = Audio(self.config["NOISE_PATH"])
        else:
            self.shock_sound = EmptyAudio()

        if self.config["SHOCK"] == "TRUE":
            self.shock = Shocker(num_shocks=int(self.config["NUMBER_OF_SHOCK_REPETITIONS"]),
                                 time_between=float(self.config["WAIT_NEXT_SHOCK"]))
        else:
            self.shock = Empty_Shocker()
        self.log.debug(",".join([str(v) for v in self.shock_times]))

    def init_game(self):
        self.dir = [0, 0]

        self.last_time = None
        self.pos = self._map.start_pos[:]
        self.game_is_running = False
        self.arrows = {pygame.K_UP: [0, -1], pygame.K_DOWN: [0, 1], pygame.K_LEFT: [-1, 0], pygame.K_RIGHT: [1, 0]}

    def run(self, max_time=None):
        """
        Runs the task
        :return:
        """
        self.log.info("RUNNING TASK")
        self.steps = 0
        self.pos_list = [self.pos[:]]
        screen_size_x = self._map.num_tiles_x * self._map.tile_size + self._map.margin * (self._map.num_tiles_x + 1)
        screen_size_y = self._map.num_tiles_y * self._map.tile_size + self._map.margin * (self._map.num_tiles_y + 1)
        if self.config["FULLSCREEN"] == "TRUE":
            self.screen = pygame.display.set_mode([0, 0], pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((screen_size_x, screen_size_y), pygame.NOFRAME)

        # self.minX = self.screen.get_width()
        # self.minY = self.screen.get_height()
        self.main_loop(max_time)
        # pygame.quit()
        if self.game_is_running:
            self.log.info("TIME RAN OUT")
        else:
            self.log.info("GOAL REACHED")
        self.log.info("PATH USED:")
        self.log.info(str(self.pos_list))
        return self.pos_list

    def main_loop(self, max_time):
        """
        Runs main task_loop
        :return:
        """
        self.game_is_running = True
        self.elapsed_time_clock = core.Clock()
        time_limit = True
        if max_time == None:
            countdown = core.CountdownTimer(0)
            time_limit = False
        else:
            countdown = core.CountdownTimer(max_time)

        self.start_time = countdown.getTime()
        audio_countdown = self.start_time - uniform(self.ISI_MIN, self.ISI_MAX)
        shock_countdown = self.start_time - self.shock_times[self.current_shock]

        # curr = time.time()
        # n=0.0

        self.dir = [0, 0]
        # clear event cache
        pygame.event.get()
        self.save_data()
        while self.game_is_running and (not time_limit or countdown.getTime() > 0):

            self.dir = self.check_keys()
            if self.save_con == "KEY" and self.dir != [0, 0]:
                self.save_data()
            prev_pos = self.pos[:]
            self.move(self.dir)
            if self.save_con == "MOVE" and prev_pos != self.pos:
                self.save_data()

            if not self.check_goal():
                audio_countdown = self.check_sound(countdown, audio_countdown)
                shock_countdown = self.check_shock(countdown, shock_countdown)
            self.draw()

            if self.check_goal() and (self.config["STOP_ON_GOAL"] == "TRUE"):
                self.game_is_running = False

                # n+=1
                # print int(n/(time.time()-curr))
        self.draw()
        phase_duration = self.start_time - countdown.getTime()
        self.log.debug('startTime: ' + str(self.start_time) + ' endTime: ' + str(countdown.getTime()) + ' dur:' + str(phase_duration))
        self.csv_writer_phaseDur.write_line([self.block_number, self.trial_number, self.phase_number, phase_duration])
        pygame.time.wait(500)

    def check_sound(self, clk, next_audio):
        """
        Checks if sound should be played
        :param clk:
        :param next_audio:
        :return:
        """
        if clk.getTime() < next_audio:
            self.shock_sound.play(self.sound_time)
            next_audio = clk.getTime() - (self.sound_time + uniform(self.ISI_MIN, self.ISI_MAX))
        return next_audio

    def check_shock(self, clk, next_shock):
        if clk.getTime() < next_shock:
            if self.current_shock < len(self.shock_times) - 1:
                self.log.debug("SHOCK AT %s" % (self.start_time - clk.getTime()))
                self.shock.shock()
                self.current_shock += 1

                next_shock = self.start_time - self.shock_times[self.current_shock]
        return next_shock

    def check_goal(self):
        """
        Checks if goal has been reached
        :return: True if yes
        """
        if self._map.field[self.pos[0], self.pos[1]] == Map.GOAL:
            return True
        return False

    def save_data(self):
        self.elapsed_time = self.elapsed_time_clock.getTime()
        self.posx = self.pos[0]
        self.posy = self.pos[1]
        self.movx = self.dir[0]
        self.movy = self.dir[1]
        self.is_goal = self.check_goal()
        if self.last_time == None:
            self.rt = "NA"
        else:
            self.rt = self.elapsed_time - self.last_time
        self.last_time = self.elapsed_time

        v = [self.subject_ID, self.condition, self.block_number, self.trial_number, self.phase_number, self.name, self.posx, self.posy, self.is_goal, self.steps, self.rt]
        # append goals x and y
        for goal in self._map.goals:
            v.append(goal[0])
            v.append(goal[1])
        # v.append(str(self.field).replace(',','').replace('\n',''))
        # v=[self.trial_number,self.phase_number,self.posx,self.posy,self.movx,self.movy,self.rt,self.elapsed_time]
        self.csv_writer.write_line(v)

    def draw(self):
        """
        Draws the field and current location marking
        :return:
        """
        self.screen.fill(self._map.background_color)
        minX = int(self.screen.get_width() / 2 - float(self._map.num_tiles_x) / 2 * (self._map.tile_size + self._map.margin))
        minY = int(self.screen.get_height() / 2 - float(self._map.num_tiles_y) / 2 * (self._map.tile_size + self._map.margin))
        for i in range(self._map.num_tiles_x):
            for j in range(self._map.num_tiles_y):
                # col = pygame.Color(255,255,255,255)
                if self._map.field[i, j] in self._map.special_color_map:
                    if self._map.field[i, j] == Map.GOAL and self.pos != [i, j]:
                        col = self._map.special_color_map[Map.EMPTY]
                    else:
                        col = self._map.special_color_map[self._map.field[i, j]]
                pygame.draw.rect(self.screen, col, (minX + (i) * (self._map.tile_size + self._map.margin) + self._map.margin,
                                                    minY + (j) * (self._map.tile_size + self._map.margin) + self._map.margin,
                                                    self._map.tile_size,
                                                    self._map.tile_size))

        pygame.draw.circle(self.screen, pygame.Color(255, 255, 0, 0),
                           (minX + self.pos[0] * (self._map.tile_size + self._map.margin) + self._map.margin + self._map.tile_size / 2,
                            minY + self.pos[1] * (self._map.tile_size + self._map.margin) + self._map.margin + self._map.tile_size / 2),
                           self._map.tile_size / 3)

        pygame.display.update()

    def move(self, dir):
        """
        Calculates next position and saves moved path
        4 Possibilities:
        -If the subject does not move nothing happens
        -If the subject moves outside the playing field hit_edge is called and nothing is done
        -If the subject moves to a wall field(if there are wall fields?) hit_wall is called and nothing is done
        -Otherwise the position is updated and appended to the saved positions and steps is incremented.
        :param dir: List with [x,y] movement
        :return:
        """

        next_pos = [self.pos[0] + dir[0], self.pos[1] + dir[1]]
        if dir[0] == 0 and dir[1] == 0:
            return
        elif next_pos[0] >= self._map.num_tiles_x or next_pos[0] < 0 or next_pos[1] >= self._map.num_tiles_y or next_pos[1] < 0:
            self.hit_edge(dir)
        elif self._map.field[next_pos[0], next_pos[1]] == Map.WALL:
            self.hit_wall(dir)
        else:
            self.pos = next_pos[:]
            self.pos_list.append(self.pos)
            self.steps += 1

    def check_keys(self):
        """
        Checks pressed keys and adds up movement values.
        This leads to following behaviour (in theory, have to test):
        If user presses left and right key the same time nothing happens
        And no values are saved.
        :return: movement_direction
        """
        move_dir = [0, 0]
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    core.quit()
                    pygame.quit()
                    sys.exit(0)
                elif event.key in self.arrows:
                    add_dir = self.arrows[event.key]
                    move_dir[0] = move_dir[0] + add_dir[0]
                    move_dir[1] = move_dir[1] + add_dir[1]
            if event.type == pygame.QUIT:
                core.quit()
                pygame.quit()
                sys.exit(0)

        return move_dir

    def hit_edge(self, dir):
        """
        Function in case we want to do something if the subject hits the edge of the grid
        :param dir:
        :return:
        """
        pass

    def hit_wall(self, dir):
        """
        Function in case we want to do something if the subject hits a wall
        :param dir:
        :return:
        """
        pass

    def draw_path(self, path=None):
        if path == None:
            path = self.pos_list
        try:
            import matplotlib.pyplot as plt
            import random
            pathX = [v[0] + 0.25 * random.random() for v in path]
            pathY = [self._map.num_tiles_y - v[1] + 0.25 * random.random() for v in path]

            plt.plot(pathX, pathY, 'go-')
            plt.xlim((-1, self._map.num_tiles_x + 1))
            plt.ylim((-1, self._map.num_tiles_y + 1))
            plt.show()
        except:
            pass


class Rating:
    def __init__(self, config, filename):
        self.config = config
        self.win = visual.Window(fullscr=True, pos=(0, 0), units="norm", color="Black")
        self.file = open(filename, 'w', encoding="UTF-8")

    def run(self):
        # Show rating
        rating = self._create_rating(self.config['TEXT'])
        print rating
        self.file.write(unicode('Rating: ' + str(rating) + '\n'))
        self.file.close()
        #self.win.fullscr = False
        #self.win.winHandle.minimize()
        self.win.flip()
        self.win.close()


    def _create_rating(self, text):
        ratingScale = visual.RatingScale(self.win, scale=text, choices=[1, 2, 3, 4, 5, 6, 7],
                                         leftKeys='left', rightKeys='right', acceptKeys='space', markerStart=3,
                                         marker="slider", markerColor="LightGrey", showAccept=False, pos=(0, 0))
        lowAnchorText = visual.TextStim(self.win, 'Not at all', pos=(-0.45, -0.2), color=[200, 200, 200],
                                        colorSpace='rgb255', height=0.075)
        highAnchorText = visual.TextStim(self.win, 'Very', pos=(0.45, -0.2), color=[200, 200, 200], colorSpace='rgb255',
                                         height=0.075)
        while ratingScale.noResponse:
            keys = event.getKeys(['q', 'ctrl'], modifiers=True)
            for key in keys:
                if key[0] == 'q' and key[1]['ctrl'] == True:
                    core.quit()
            ratingScale.draw()
            lowAnchorText.draw()
            highAnchorText.draw()
            self.win.flip()
        rating = ratingScale.getRating()
        return rating


def main(dlg_data=None, config=None):
    if config is None:
        config = Priority_Dict(CONFIG_PATH)
    ID = "NA"
    COND = "NA"
    DATE = "NA"
    if config["DIALOG_BOX"] == "TRUE":
        if dlg_data is None:
            dia = DialogBox()
            vals = dia.show_dlg()
        else:
            vals = dlg_data
        ID = vals[0]
        COND = vals[1]
        #DATE = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        DATE = vals[3].replace('.', '') + '_' + vals[4].replace(':', '')

    instruction_screen = Pause_Screen(config.get_dict("INSTRUCTIONS"))
    pause_screen = Pause_Screen(config.get_dict("PAUSE_SCREEN"))
    end_screen = Pause_Screen(config.get_dict("END_SCREEN"))

    instruction_screen.show()

    num_blocks = int(config["BLOCKS"])
    num_trials = int(config["TRIALS_PER_BLOCK"])
    num_phases = int(config["PHASES_PER_TRIAL"])

    config.set_phase(0)  # for initialization
    ebt = EscapeBehaviourTest(config, 0, 0, 0, subject_ID=ID, condition=COND, start_time=DATE)

    map_config = config.get_dict("MAP_CONFIG")
    random_map_config = config.get_dict("RANDOM")

    if config['EXPLORATION_PHASE'] == "TRUE":
        exploration_map_config = config.get_dict("EXPLORATION_MAP")
        map_ = Map.empty(map_config, exploration_map_config)
        config.set_phase(0)
        ebt.reload(0, 0, 0, config=config, map_=map_)
        ebt.run(float(config["DURATION"]) / 1000)
        pause_screen.show()

    for block_number in range(1, num_blocks+1):
        map_ = None
        if config["RANDOM_MAP_ON_BLOCK"] == "TRUE" or block_number is 1:
            map_ = Map.random(map_config, random_map_config)

        for trial_number in range(1, num_trials+1):
            for phase_number in range(1, num_phases + 1):
                config.set_phase(phase_number)
                ebt.reload(block_number, trial_number, phase_number, config=config, map_=map_)
                ebt.run(float(config["DURATION"]) / 1000)
            pause_screen.show()

            # Show pause screen (except last trial)
            #if block_number is not num_blocks and trial_number is not num_trials:
                #pause_screen.show()

    # Close task (resolves input error on rating)
    pygame.quit()

    # Show Rating
    filename = os.path.dirname(__file__) + '/output/' + ID + '_' + DATE + '.txt'
    print(filename)
    r = Rating(config.get_dict('RATING'), filename)
    r.run()

    # Show endscreen and close task again
    end_screen.show()
    pygame.quit()


if __name__ == "__main__":
    # load config
    script_dir = os.path.dirname(__file__)
    os.chdir(script_dir + "/..")
    config = Priority_Dict(CONFIG_PATH)  # Exploration -> NoStress -> Stress
    if len(sys.argv) > 1:
        # Load data from file
        filename = sys.argv[1]
        print filename
        data = pickle.load(open(filename, 'rb'))
        main(dlg_data=data, config=config)
    elif config["DIALOG_BOX"] == "TRUE":
        # Display dialog
        dlg = DialogBox()
        data = dlg.show_dlg()
        # run
        main(dlg_data=data, config=config)
    else:
        main()
