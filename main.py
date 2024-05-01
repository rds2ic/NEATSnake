"""
TODO:
Fix algorithm to check if body parts are left, right, or ahead of the head
"""
import os
import pygame
import random
import neat
import math
import pickle

WIDTH = HEIGHT = 800
FPS = 240
PIXEL_WIDTH = 40
RED = (220, 20, 60)
GREEN = (128, 255, 0)
PURPLE = (128, 0, 128)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Snake:
    def __init__(self) -> None:
        self.body = [] # Array storing snake body bits
        self.randomisePos()
        self.body[0].makeHead() # Marks the first body as the head
    
    def draw(self, win:pygame.Surface) -> None:
        # Draws each body part
        for body in self.body:
            body.draw(win)
    
    def move(self, dir: int) -> None:
        i, j = self.body[0].returnPos() # Coordinates of the head
        posDirections = [(i, j-1), (i+1, j), (i, j+1), (i-1, j)] # Helper Array
        self.body.insert(0, SnakeBody(posDirections[dir][0], posDirections[dir][1])) # Adds a body part in the direction it is moving
        # Update head and old head
        self.body[0].makeHead() 
        self.body[1].makeBody()
        # Remove last body bit
        self.body.pop()
    
    def grow(self, dir: int) -> None:
        i, j = self.body[len(self.body)-1].returnPos() # Coordinates of end of snake
        posDirections = [(i, j+1), (i-1, j), (i, j-1), (i+1, j)] # Helper Array
        self.body.append(SnakeBody(posDirections[dir][0], posDirections[dir][1])) # Adds a body part in the opposite of the direction it is moving
    
    def randomisePos(self):
        self.body.append(SnakeBody(random.randint(0, WIDTH//PIXEL_WIDTH-1), random.randint(0, WIDTH//PIXEL_WIDTH-1))) # Adds a body part at a random point
    
    def returnSize(self):
        return len(self.body) # Length of the snake
    
    def returnBodyPoss(self):
        bodyPoss = []
        for body in self.body:
            bodyPoss.append(body.returnPos())
        return bodyPoss

class SnakeBody:
    def __init__(self, i: int, j: int) -> None:
        # Coordinates
        self.i = i
        self.j = j
        # x and y values for drawing
        self.x = i * PIXEL_WIDTH
        self.y = j * PIXEL_WIDTH
        self.rect = pygame.Rect(self.x, self.y, PIXEL_WIDTH, PIXEL_WIDTH) # pygame rect value
        self.colour = GREEN

    def draw(self, win:pygame.Surface) -> None:
        # Draws the rect value
        pygame.draw.rect(win, self.colour, self.rect)
    
    def makeHead(self) -> None:
        # Makes a body part the head
        self.colour = PURPLE
    
    def makeBody(self) -> None:
        # Makes the head a normal body part
        self.colour = GREEN
    
    def returnPos(self) -> tuple[int, int]:
        return (self.i, self.j) # returns the coordinates of the body bit

class Food:
    def __init__(self, snake: Snake) -> None:
        self.randomisePos(snake) # Randomises position
    
    def draw(self, win:pygame.Surface) -> None:
        pygame.draw.rect(win, RED, self.rect) # Draws rect
    
    def returnPos(self):
        return self.i, self.j # Returns coordinates of food 
    
    def randomisePos(self, snake: Snake):
        validPosition = False # Bool value to check if the generated value is possible
        while not validPosition: 
            # Loops through until a possible value is found
            validPosition = True
            # Generating random values for the food coordinates
            i = random.randint(0, WIDTH//PIXEL_WIDTH-1)
            j = random.randint(0, WIDTH//PIXEL_WIDTH-1)
            for body in snake.body:
                # Checks for each value if the position is the same as a snake body bit and if so restart the loop
                if (i, j) == body.returnPos():
                    validPosition = False
        # Initialising the other values once possible values are found
        self.i = i
        self.j = j
        self.x = i * PIXEL_WIDTH
        self.y = j * PIXEL_WIDTH
        self.rect = pygame.Rect(self.x, self.y, PIXEL_WIDTH, PIXEL_WIDTH)

class Game:
    def __init__(self) -> None:
        pygame.init()
        self.snake = Snake() # Intialise the snake
        self.initialPos = self.snake.body[0].returnPos()
        self.food = Food(self.snake) # Intialise the food
        self.win = pygame.display.set_mode((WIDTH, HEIGHT)) # Intialise the game window
        pygame.display.set_caption('SNAKE')
        self.clock = pygame.time.Clock()
        firstDirection = [self.snake.body[0].returnPos()[1], (WIDTH//PIXEL_WIDTH-1) - self.snake.body[0].returnPos()[0], (WIDTH//PIXEL_WIDTH-1) - self.snake.body[0].returnPos()[1], self.snake.body[0].returnPos()[0]]
        # Choose the best option for the snake to first move in
        self.direction = firstDirection.index(max(firstDirection)) # 0 - NORTH | 1 - EAST | 2 - SOUTH | 3 - WEST
    
    def updateDisplay(self):
        # Draws all the objects and then ticks the clock
        self.win.fill(BLACK)
        self.snake.draw(self.win)
        self.food.draw(self.win)
        pygame.display.update()
        self.clock.tick(FPS)

    def returnGameState(self):
        # Produces the inputs for the neural network
        i, j = self.snake.body[0].returnPos()
        # Array storing 1 or 0 for each heading if there is a wall in the given heading, index refers to self.direction value, ie NORTH is 0
        wallArr = [1 if j == 0 else 0, 1 if i == (WIDTH//PIXEL_WIDTH-1) else 0,
                    1 if j == (WIDTH//PIXEL_WIDTH-1) else 0, 1 if i == 0 else 0]
        # Array storing 1 or 0 for each heading if there is a body part in the given heading
        bodyArr = [1 if (i, j-1) in self.snake.returnBodyPoss() else 0, 1 if (i+1, j) in self.snake.returnBodyPoss() else 0,
                   1 if (i, j+1) in self.snake.returnBodyPoss() else 0, 1 if (i-1, j) in self.snake.returnBodyPoss() else 0]
        # Array storing 1 or 0 for each heading if there is food in the given heading
        foodArr = [1 if self.food.returnPos()[1] < j else 0, 1 if self.food.returnPos()[0] > i else 0,
                   1 if self.food.returnPos()[1] > j else 0, 1 if self.food.returnPos()[0] < i else 0]

        return (wallArr[self.direction] or bodyArr[self.direction], wallArr[self.turnLeft()] or bodyArr[self.turnLeft()],
                wallArr[self.turnRight()] or bodyArr[self.turnRight()], foodArr[self.direction], foodArr[self.turnLeft()], foodArr[self.turnRight()])
    
    def turnLeft(self, turns=1):
        return (self.direction - turns) % 4
    
    def turnRight(self, turns=1):
        return (self.direction + turns) % 4

    def loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit(0)
                
        self.snake.move(self.direction)

        head = self.snake.body[0]

        for i, body in enumerate(self.snake.body):
            if body.returnPos() == head.returnPos() and i != 0:
                return True

        if head.returnPos()[0] < 0 or head.returnPos()[0] > (WIDTH // PIXEL_WIDTH - 1) or head.returnPos()[1] < 0 or head.returnPos()[1] > (WIDTH // PIXEL_WIDTH - 1):
            return True
        
        if len(self.snake.body) >= ((WIDTH // PIXEL_WIDTH)**2):
            return True

        if self.snake.body[0].returnPos() == self.food.returnPos():
            self.snake.grow(self.direction)
            self.food.randomisePos(self.snake)
        
        return False

    def trainAI(self, genome, config):
        net = neat.nn.FeedForwardNetwork.create(genome, config) # Creating the neural network

        running = True
        # count stores amount of times a snake makes a same turn, if it is too many it terminates otherwise it will be stuck in a loop
        repeatCount = 0
        cellsVisited = 1
        visited = [self.snake.body[0].returnPos()]
        oldDecision = -1
        count = 0
        oldSize = 1
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit(0)
            
            output = net.activate(self.returnGameState()) # Passing the inputs to the neural network
            decision = output.index(max(output)) # Gets the index of the highest activation | 0 turn left | 1 stay straight | 2 turn right
            if decision == 0:
                self.direction = self.turnLeft()
            if decision == 2:
                self.direction = self.turnRight()
            # print(output)

            over = self.loop()
            self.updateDisplay()

            if self.snake.body[0].returnPos() not in visited:
                cellsVisited += 1
                visited.append(self.snake.body[0].returnPos())

            if decision == oldDecision:
                repeatCount += 1
            elif decision != 1:
                repeatCount = 0

            if decision != 1:
                oldDecision = decision

            if len(self.snake.body) > oldSize:
                repeatCount = 0
                count = 0
                oldSize = len(self.snake.body)

            count += 1

            # Need to calculate fitness
            if over or repeatCount > 10 or count > 100:
                self.calculateFitness(genome, cellsVisited)
                break
    
    def calculateFitness(self, genome, cellsVisited):
        genome.fitness += len(self.snake.body) # + 2 * math.log1p(cellsVisited) + abs(self.snake.body[0].returnPos()[0] + self.snake.body[0].returnPos()[1] - self.food.returnPos()[0] - self.food.returnPos()[1])

    def testAI(self, genome, config):
        net = neat.nn.FeedForwardNetwork.create(genome, config) # Creating the neural network

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit(0)
            
            output = net.activate(self.returnGameState()) # Passing the inputs to the neural network
            decision = output.index(max(output)) # Gets the index of the highest activation | 0 turn left | 1 stay straight | 2 turn right
            if decision == 0:
                self.direction = self.turnLeft()
            if decision == 2:
                self.direction = self.turnRight()

            over = self.loop()
            self.updateDisplay()

def evalGenomes(genomes, config):
    for genome_id, genome in genomes:
        genome.fitness = 0.0
        game = Game()
        game.trainAI(genome, config)

def runNeat(config):
    # p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-54')
    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(5))

    winner = p.run(evalGenomes)
    # Saves vest neural network
    with open("best.pickle", "wb") as f:
        pickle.dump(winner, f)

def testAI(config):
    with open("best.pickle", "rb") as f:
        winner = pickle.load(f)
    game = Game()
    game.testAI(winner, config)

if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    configPath = os.path.join(local_dir, 'config-feedforward')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         configPath)
    runNeat(config) # Comment out when neural network is saved
    # testAI(config)
