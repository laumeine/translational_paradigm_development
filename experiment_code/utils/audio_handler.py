import pygame
import pygame.mixer as mixer
import logging
import time
import os.path


class Audio:
    def __init__(self, file_path):
        self.file_path = file_path
        mixer.quit()
        if mixer.get_init() is None:
            logging.info("INITIALIZING SOUND MIXER")
            if not os.path.isfile(file_path):
                logging.error("AUDIO FILE NOT FOUND!")
            pygame.mixer.pre_init(44100, -16, 1, 512)
            mixer.init()
        self.sound = mixer.Sound(file_path)

    def play(self, max_time=0):
        self.sound.stop()
        self.sound.play(maxtime=int(1000.0 * max_time))

    def stop(self):
        self.sound.stop()


class EmptyAudio:
    def __init__(self, *args):
        pass

    def play(self, max_time=0):
        pass

    def stop(self):
        pass


if __name__ == "__main__":
    audio = Audio("noise.wav")

    for i in range(10):
        audio.play(0.5)
        for j in range(5500):
            pass

    time.sleep(5)
