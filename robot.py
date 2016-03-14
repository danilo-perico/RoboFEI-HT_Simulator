import init
import pygame
from math import cos
from math import sin
from math import radians
from math import sqrt
from math import atan2
from math import pi
from math import exp

class Robot():
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.new_x = x
        self.new_y = y
        self.front = 0
        self.rotate = 0
        self.index = 0
        self.radius = 22
        self.front = 0
        self.rotate = 0
        self.collision = False

    def draw_robot(self,robot_index):
        pygame.draw.circle(init.screen,init.BLACK,(self.x ,self.y),self.radius,0)
        pygame.draw.circle(init.screen,init.BLUE,(self.x ,self.y),self.radius-2,0)
        x_theta = cos(radians(self.rotate))*(self.radius-2)
        y_theta = sin(radians(self.rotate))*(self.radius-2)
        pygame.draw.line(init.screen,init.BLACK,(self.x ,self.y),(self.x + x_theta, self.y - y_theta),3)
        font = pygame.font.Font(None, 20)
        self.index = robot_index + 1
        robot_name = "B" + str(self.index)
        text = font.render(robot_name, 1, (10, 10, 10))
        textpos = (self.x - 5, self.y - 40)
        init.screen.blit(text, textpos)

    def motion_model(self,front,rotate):
        self.front = front
        self.rotate = (self.rotate + rotate) % 360

        if self.collision and self.front == 1:
            self.front = -1
        elif self.collision and self.front == -1:
            self.front = 1

        self.new_x += cos(radians(self.rotate))*self.front
        self.new_y -= sin(radians(self.rotate))*self.front

        self.x = int(self.new_x)
        self.y = int(self.new_y)

        if self.x > 1040:
            self.x = 1040
            self.new_x = 1040
        elif self.x < 0:
            self.x = 0
            self.new_x = 0

        if self.y > 740:
            self.y = 740
            self.new_y = 740
        elif self.y < 0:
            self.y = 0
            self.new_y = 0

        self.collision = False

    def kick(self, ball):
        d = sqrt((self.x - ball.x)**2+(self.y - ball.y)**2)
        r = atan2((ball.y-self.y), (ball.x-self.x))*180/pi
        force = 10 * exp(-2.3/ball.radius*d+2.3/ball.radius*(self.radius+ball.radius))
        ball.put_in_motion(force, r)


    def draw_vision(self,rotate):
        field_of_view = 101.75
        vision_dist = 200

        startRad = radians(-35-rotate)
        endRad = radians(35-rotate)
        pygame.draw.arc(screen, (255, 255, 255), [self.x-vision_dist,self.y-vision_dist,vision_dist*2,vision_dist*2], startRad, endRad, 1)

        vision_surface = pygame.Surface((vision_dist * 2, vision_dist * 2))
        vision_surface.fill([0,150,0])
        vision_surface.set_colorkey([0,150,0])
        vision_surface.set_alpha(200)
        vision_surface_center = (vision_dist, vision_dist)

        #print rotate
        #print self.theta
        theta_vision = radians(rotate)

        angle_1 = theta_vision - field_of_view/2
        angle_2 = theta_vision + field_of_view/2

        point_1 = (vision_dist, angle_1)
        point_2 = (vision_dist, angle_2)

        point_1 = toRectangular(point_1)
        point_2 = toRectangular(point_2)

        point_1 = (point_1[0] + vision_surface_center[0], point_1[1] + vision_surface_center[1])
        point_2 = (point_2[0] + vision_surface_center[0], point_2[1] + vision_surface_center[1])


        pygame.draw.arc(vision_surface, (255, 255, 255), [vision_dist/2,vision_dist/2,vision_dist,vision_dist], startRad, endRad, 1)

        pygame.draw.line(vision_surface, (255, 255, 255), vision_surface_center, point_1, 1)
        pygame.draw.line(vision_surface, (255, 255, 255), vision_surface_center, point_2, 1)


        position = (
            self.x - vision_dist,
            self.y - vision_dist
        )

        screen.blit(vision_surface, position)


    def hcc(self,x1,y1,x2,y2):
        return sqrt((x1-x2)**2 + (y1-y2)**2)


    def distD(self, x1, y1, x2, y2):
        return self.hcc(x1, y1, x2, y2)

    def distR(self, x1, y1, x2, y2):
        return atan2((y2-y1), (x2-x1))*180/pi
        # atan2 retorna angulo entre -pi e +pi

    def compAng(self, ang, base):
        angrange = 35
        if(base > 180-angrange or base < -180+angrange):
            if(ang > 0 and base < 0):
                return (ang < base + 360 + angrange) and (ang > base + 360 - angrange)
            elif (ang < 0 and base > 0):
                return (ang < base - 360 + angrange) and (ang > base - 360 - angrange)
        return (ang < base + angrange) and (ang > base - angrange)


    def view_obj(self,x,y,rotate):
        field_of_view = 100
        vision_dist = 200  #we need to add as global variavel

        d = self.distD(self.x,self.y,x,y)
        r = self.distR(self.x,self.y,x,y)

        d=random.gauss(d,0.1*d/10)

        if((d < vision_dist) and self.compAng(r,rotate)):
            print 'Inside'
        else:
            print 'Outside'









