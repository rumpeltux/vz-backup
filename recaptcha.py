#!/usr/bin/env python
import pygame
import re, os

def extract_key(data):
    m = re.compile(r'challenge\?k=(\w+)').search(data)
    if m: return m.group(1)

def has_captcha(data):
    return '<div id="recaptcha_image"' in data

class Solver:
    pass

class GUISolver(Solver):
    def solve(self, challenge, image):
        img_file = challenge+".jpg"
        open(img_file, "w").write(image)
      	graphic = pygame.image.load(img_file)
        os.unlink(img_file)

        screen = pygame.display.set_mode(graphic.get_size())
        screen.blit(graphic.convert(), (0, 0))
        pygame.display.flip()

        captcha = raw_input("Solve Captcha :")
        pygame.display.quit()
        return captcha

DefaultSolver = GUISolver

class ReCaptcha:
    def __init__(self, browser, data=None, key=None, solver=None):
        if solver is None: solver = DefaultSolver()
        if data: key = extract_key(data)
        if key is None: raise TypeError("either data or key argument has to be set")

        self.solver = solver
        self.br  = browser
        self.k   = key
        
    def solve(self):
        challenge = self.get_challenge()
        image = self.get_image(challenge)
        key = self.solver.solve(challenge, image)
        return (challenge, key)
        
    def get_challenge(self):
        pat = re.compile(r"challenge\s*:\s*'([\w\-]+)'")
        for line in self.br.open('http://www.google.com/recaptcha/api/challenge?k=' + self.k):
            m = pat.search(line)
            if m: return m.group(1)
    
    def get_image(self, challenge):
		return self.br.open("http://www.google.com/recaptcha/api/image?c=" + challenge).read()

if __name__ == "__main__":
    import sys 
    import mechanize

    print "challenge: %s\nkey: %s" % ReCaptcha(browser=mechanize.Browser(), key=sys.argv[1]).solve()
