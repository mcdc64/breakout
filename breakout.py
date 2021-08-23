import numpy as np
import pygame
from pygame.locals import K_p

class Block(pygame.sprite.Sprite):
    def __init__(self,centre_x,centre_y,scale_y,hypradius,is_paddle=False): #the blocks are hyperellipses with n = 4. This gives them a "rounded rectangle" shape to make bounces more interesting
        super(Block,self).__init__()

        self.c_x = centre_x
        self.c_y = centre_y
        self.s_y = scale_y
        self.hypradius = hypradius
        self.hidden = False
        self.is_paddle = is_paddle

        self.block_width = int(2*hypradius)
        self.block_height = int(2*hypradius/scale_y)

        self.image = pygame.transform.scale(pygame.image.load("images/block_sprite.png"),(self.block_width,self.block_height))

        if(is_paddle):
            self.image = pygame.transform.scale(pygame.image.load("images/paddle_sprite.png"),(self.block_width,self.block_height))

        self.rect = pygame.Rect(self.c_x - self.block_width / 2, self.c_y - self.block_height / 2, self.block_width,self.block_height)
        self.image_rect = pygame.Rect(self.c_x, self.c_y, self.block_width, self.block_height)
        #self.image.fill()

    def intersection_eq (self,ball,d): #returns how "far" the eqn of the hyperellipse is from matching its RHS. Will use this to tell us the best "matching" value of d.
        surd = self.hypradius**4 - (self.s_y * d)**4
        if(ball.pos_x < self.c_x):
            value = (-np.sqrt(np.sqrt(surd)) + (self.c_x - ball.pos_x)) ** 2 + (d + self.c_y - ball.pos_y) ** 2
            return (value - ball.radius**2)
        value = (np.sqrt(np.sqrt(surd)) + (self.c_x - ball.pos_x))**2 + (d+self.c_y-ball.pos_y)**2
        return (value - ball.radius**2)

    def get_intersection(self,ball):
        numpoints = 25
        d_vals = np.linspace(0,ball.pos_y - self.c_y,numpoints) #we define d as y - self.c_y where y is the y coord of the intersection
        min_idx = 0
        min_diff = 10000
        for i in range(0,numpoints):
            curr_diff = np.abs(self.intersection_eq(ball,d_vals[i]))
            if min_diff > curr_diff:
                min_diff = curr_diff
                min_idx = i
        best_d = d_vals[min_idx]
        out_y = best_d + self.c_y
        best_c = np.sqrt(np.sqrt(self.hypradius**4 - (self.s_y * best_d)**4))
        if (ball.pos_x < self.c_x):
            best_c = -best_c
        out_x = best_c + self.c_x

        return np.asarray([out_x,out_y])

    def get_normal(self,x,y): #gets the normal at a particular point on the hyperellipse, with level sets
        return 4*np.asarray([(x-self.c_x)**3,(self.s_y**4)*(y-self.c_y)**3])

    def update(self):
        if (self.is_paddle):
            self.image = pygame.transform.scale(pygame.image.load("images/paddle_sprite.png"),(self.block_width,self.block_height))
            self.rect = pygame.Rect(self.c_x - self.block_width / 2, self.c_y - self.block_height / 2, self.block_width,self.block_height)

    def draw(self,screen):
        screen.blit(self.image, self.rect)

    def hide(self):
        self.hidden = True

class Ball(pygame.sprite.Sprite):

    def __init__(self,pos_x,pos_y,vel_x,vel_y,radius): #the ball has position and velocity vectors, and a radius (it is a circle)
        super(Ball, self).__init__()
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.radius = radius
        self.image = pygame.image.load("images/ball_sprite.png")
        self.rect = pygame.Rect(self.pos_x - radius, self.pos_y - radius, 2*radius,2*radius)
        self.image_rect = pygame.Rect(self.pos_x, self.pos_y, 2*radius,2*radius)

    def update(self):
        self.image = pygame.transform.scale(pygame.image.load("images/ball_sprite.png"),(2*self.radius,2*self.radius))
        self.rect = pygame.Rect(self.pos_x - self.radius, self.pos_y - self.radius, 2*self.radius,2*self.radius)


    def collides(self,block): #simply assume the block is a rectangle for the purposes of calculating collisions (should be a good approximation)

        if(np.abs(block.c_x - self.pos_x) < block.hypradius+self.radius):
            if(np.abs(block.c_y - self.pos_y) < (block.hypradius/block.s_y) + self.radius):

                return True
        return False

    def reflect(self,refl_vect,speed): #find integer coordinates near the ball (where blocks can be located)

        velocity = np.asarray([self.vel_x,self.vel_y])
        subtraction_factor = ((np.dot(velocity,refl_vect))/(np.dot(refl_vect,refl_vect)))*refl_vect
        refl_velocity = velocity - 2*subtraction_factor
        refl_velocity = refl_velocity*(speed/np.linalg.norm(refl_velocity)) #make sure speed is conserved
        self.vel_x = refl_velocity[0]
        self.vel_y = refl_velocity[1]

    def find_nearby_blocks(self,hypradius,yscale,multiple):

        low_x = (round(self.pos_x - (self.radius+hypradius)-0.1)//multiple)*multiple
        low_y = (round(self.pos_y - (self.radius + hypradius/yscale)-0.1)//multiple)*multiple
        up_x = (round(self.pos_x + (self.radius+hypradius)+0.1)//multiple)*multiple
        up_y = (round(self.pos_y + (self.radius + hypradius / yscale)+0.1)//multiple)*multiple
        out_list = []
        for i in range(low_x,up_x,multiple):
            for j in range(low_y,up_y,multiple):
                out_list.append((i,j))
        return np.asarray(out_list)

    def draw(self,screen):
        screen.blit(self.image, self.rect)

pygame.init()
pygame.display.set_caption("Breakout")

block_dict = {} #use a dictionary to store all the blocks in the game - makes it easy to find them when checking for collisions

screen_width = 1400
screen_height = 920

# Set up the drawing window
screen = pygame.display.set_mode([screen_width,screen_height])



no_across = 8 #ratio of no_across:no_down should be a little higher than the ratio screen_width:screen_height
no_down = 4

yscale = 2
hypradius = ((screen_width//no_across) - 10)//2

x_step = screen_width//no_across
y_step = screen_height//(3*(no_down-1)+1)

for i in range(hypradius,screen_width+hypradius,x_step):
    for j in range(hypradius//yscale,screen_height//3+1+hypradius//yscale,y_step):
        key_to_add = str(i)+"_"+str(j)
        print(key_to_add)
        print(hypradius)
        block_dict[key_to_add] = Block(i,j,yscale,hypradius)
        curr_block = block_dict[key_to_add]
        screen.blit(curr_block.image,curr_block.rect)


ball = Ball(341,513,180,240,20)

ball_speed = np.linalg.norm((180,240))

velocity_eps = 40 #minimum velocity
paddle = Block(screen_width//2,8*screen_height//10,5,150,True)
screen.blit(paddle.image,paddle.image_rect)
screen.blit(ball.image,ball.image_rect)
#print(ball.find_nearby_blocks(yscale,hypradius,10))

score = 0
combo = 0 # no. of blocks broken in succession without hitting the paddle
score_increment = 20

hidden_count = 0 # track no. of blocks broken

# Run until the user asks to quit

running = True
last_time = pygame.time.get_ticks()
paddle_collided = False
paused = False
has_won = False
has_fake_won = False

while running: #main while loop

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.locals.K_p:
                if paused:
                    paused = False
                else:
                    paused = True


    if(paused):
        last_time = pygame.time.get_ticks()
        continue
    this_time = pygame.time.get_ticks()
    delta_t = (this_time - last_time)/1000 #get time between this frame and the last. Used to update the ball position

    last_time = pygame.time.get_ticks()

    # Fill the background with black

    screen.fill((0, 0, 0))
    for key in block_dict: #draw all of the blocks in block_dict
        curr_block = block_dict[key]
        if(not block_dict[key].hidden):
            screen.blit(curr_block.image,curr_block.rect)

    ball.pos_x += ball.vel_x*delta_t
    ball.pos_y += ball.vel_y*delta_t

    ball_v = np.asarray((ball.vel_x/np.linalg.norm((ball.vel_x,ball.vel_y)),ball.vel_y/np.linalg.norm((ball.vel_x,ball.vel_y))))*ball_speed
    ball.vel_x = ball_v[0]
    ball.vel_y = ball_v[1]

    ball.update()
    ball.draw(screen)

    paddle.c_x = pygame.mouse.get_pos()[0] #move the paddle according to the mouse

    #print("Paddle: " +str(paddle.c_x)+" "+str(paddle.c_y))
    #print("Ball: "+str(ball.pos_x)+" "+str(ball.pos_y))
    if(ball.rect.colliderect(paddle.rect) and not paddle_collided): #do all the collision stuff that we need when the ball hits the paddle
        combo = 0
        paddle_collided = True
        print("Colliding")
        print("Distance:"+str(np.sqrt((ball.pos_x-paddle.c_x)**2 + (ball.pos_y - paddle.c_y)**2)))
        intersection = paddle.get_intersection(ball)
        ball.reflect(paddle.get_normal(intersection[0],intersection[1]),ball_speed) #update the ball velocity according to the normal at the point of intersection

    if(not ball.rect.colliderect(paddle.rect) and paddle_collided):
        paddle_collided = False

    if(np.abs(ball.vel_y)<velocity_eps): #if the y - velocity of the ball is too slow to reach the paddle in any meaningful time, update it
        ball.vel_y = velocity_eps * ball.vel_y/np.sign(ball.vel_y)

    if((ball.pos_x<=ball.radius and ball.vel_x<0) or(ball.pos_x>screen_width-ball.radius and ball.vel_x >0)):
        ball.vel_x = -ball.vel_x #reflect the ball if it leaves the x bounds of the screen

    for key in block_dict: #check if ball collides with blocks, reflect if so
        if(not block_dict[key].hidden):
            if ball.rect.colliderect(block_dict[key].rect):
                combo += 1
                score += score_increment*combo

                intersection = block_dict[key].get_intersection(ball)
                ball.reflect(block_dict[key].get_normal(intersection[0],intersection[1]),ball_speed)
                block_dict[key].hidden = True
                hidden_count += 1

    if(ball.pos_y <= 0 and ball.vel_y < 0): # the player "wins" if they get the ball to the top of the screen

        if(hidden_count<len(block_dict) and not has_fake_won and not has_won):
            has_fake_won = True


    if(has_fake_won and not has_won):
        false_win_text = "You broke out, but did not destroy all the blocks. Try to destroy them all for a higher score!"
        false_win_img = font.render(false_win_text, True, (0, 120, 223))
        img_dims = false_win_img.get_rect().size
        screen.blit(false_win_img,((screen_width - img_dims[0])//2,(screen_height- img_dims[1])//2))


    if (hidden_count == len(block_dict) and not has_won): #a "true" win occurs when all blocks are destroyed
        has_won = True
        score += 500 #500 extra points for destroying all blocks

    if(has_won):
        true_win_text = "You destroyed all the blocks! You win! Score:"+str(score)
        true_win_img = font.render(true_win_text, True, (0, 120, 223))
        img_dims = true_win_img.get_rect().size

        screen.blit(true_win_img,((screen_width-img_dims[0])//2,(screen_height-img_dims[1])//2))



    if(ball.pos_y>screen_height-ball.radius and ball.vel_y>0):
        ball.vel_y = -ball.vel_y
    paddle.update()
    paddle.draw(screen)

    font = pygame.font.SysFont(None, 24)
    score_img = font.render("Score: "+str(score), True, (0,120,223))
    combo_img = font.render("Combo: "+str(combo),True,(0,120,223))
    screen.blit(score_img, (50, screen_height - 100))
    screen.blit(combo_img, (50, screen_height - 50))


    # Did the user click the window close button?



    # Flip the display

    pygame.display.flip()


# Done! Time to quit.

pygame.quit()