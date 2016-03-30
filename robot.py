from screen import *
from control import *
from vision import *
import pygame
from math import cos
from math import sin
from math import radians
from math import degrees
from math import sqrt
from math import atan2
from math import exp
from random import gauss

import sys
sys.path.append('./AI/Blackboard/src/')
from SharedMemory import SharedMemory


class Robot(pygame.sprite.Sprite,Vision):
    def __init__(self, x, y, theta, KEY, color):
        pygame.sprite.Sprite.__init__(self)
        Vision.__init__(self)
        self.x = x
        self.y = y
        self.rotate = theta
        self.KEY = KEY
        self.color = color
        self.new_x = x
        self.new_y = y
        self.robot_width = 26
        self.robot_height = 26
        self.radius = 13
        self.index = 0

        self.front = 0
        self.turn = 0
        self.drift = 0
        self.in_motion = False
        self.collision = False
        self.image = pygame.Surface([self.robot_width, self.robot_height])
        self.rect = self.image.get_rect()
        #self.saved_image = self.image
        self.front = 0
        self.rect.x = x
        self.rect.y = y
        self.sum_time = 0
        self.old_x = x
        self.old_y = y

        #self.panora = Vision()
        self.view_rot = theta

        self.bkb = SharedMemory()

        self.Mem = self.bkb.shd_constructor(KEY)
        print 'Shared Memory successfully created as ',KEY
        #TODO remover a linha vision_search_ball.... como nao estou utilizando decisao ainda, estou forcando a busca..
        self.bkb.write_int(self.Mem,'VISION_SEARCH_BALL',1)
        #TODO instanciar a classe visao passando o blackboard

        self.control = CONTROL(self)
        self.ball = None

        # Errors
        # Mean = 0 for symmetrical errors
        # Variances should not be 0
        self.errors_on = False # Turn errors on and off!
        self.walk_error_mean = 0
        self.walk_error_variance = 0
        self.drift_error_mean = 0
        self.drift_error_variance = 0
        self.turn_error_mean = 0
        self.turn_error_variance = 0

        self.kick_error_angle_mean = 0
        self.kick_error_angle_variance = 0
        self.kick_error_force_mean = 0
        self.kick_error_force_variance = 0

        # IMU
        self.imu_error_mean = 0
        self.imu_error_variance = 0
        self.orientation_error = 0

    def draw_robot(self,robot_index, screen):
        self.image.fill(screen.GREEN)
        self.image.set_colorkey(screen.GREEN)

        self.rect.x = self.x - 13
        self.rect.y = self.y - 13

        #robot's body
        pygame.draw.rect(self.image, self.color, (3, 0, 16, 26), 0)

        #feet
        pygame.draw.rect(self.image, screen.BLACK, (19, 2, 5, 10), 0)
        pygame.draw.rect(self.image, screen.BLACK, (19, 14, 5, 10), 0)

        #sum time between frames
        self.sum_time = (screen.clock.get_time() + self.sum_time) % 500

        #feet movement while walking
        if self.control.action_flag != 0:
            if self.sum_time < 250:
                pygame.draw.rect(self.image, screen.BLACK, (19, 1, 6, 12), 0)
                pygame.draw.rect(self.image, screen.BLACK, (19, 14, 5, 10), 0)
            else:
                pygame.draw.rect(self.image, screen.BLACK, (19, 2, 5, 10), 0)
                pygame.draw.rect(self.image, screen.BLACK, (19, 13, 6, 12), 0)

        image2 = pygame.transform.rotate(self.image, self.rotate)

        #fix rotation to the center
        rot_rect = image2.get_rect(center=self.rect.center)

        #show
        screen.background.blit(image2, (rot_rect))

        #text
        font = pygame.font.SysFont("Arial", 15)
        self.index = robot_index + 1
        robot_name = "B" + str(self.index)
        text = font.render(robot_name, 1, (10, 10, 10))
        textpos = (self.x - 5, self.y - 40)
        screen.background.blit(text, textpos)



    '''Control'''
    def motion_vars(self, front, rotate, drift):
        self.front = front
        self.turn = rotate
        self.drift = drift


    def set_errors(self,    walk_err_mean = 0, walk_err_var = 0,
                            turn_err_mean = 0, turn_err_var = 0,
                            drift_err_mean = 0, drift_err_var = 0,
                            kick_ang_err_mean = 0, kick_ang_err_var = 0,
                            kick_force_err_mean = 0, kick_force_err_var = 0,
                            imu_err_mean = 0, imu_err_var = 0):
        self.errors_on = True
        self.walk_error_mean = walk_err_mean
        self.walk_error_variance = walk_err_var
        self.turn_error_mean = turn_err_mean
        self.turn_error_variance = turn_err_var
        self.drift_error_mean = drift_err_mean
        self.drift_error_variance = drift_err_var
        self.kick_error_angle_mean = kick_ang_err_mean
        self.kick_error_angle_variance = kick_ang_err_var
        self.kick_error_force_mean = kick_force_err_mean
        self.kick_error_force_variance = kick_force_err_var
        self.imu_error_mean = imu_err_mean
        self.imu_error_variance = imu_err_var

    def motion_model(self, lines, goals, robots):
        turn = self.turn
        if self.errors_on and self.in_motion:
            turn += gauss(self.turn_error_mean, self.turn_error_variance)

        front = self.front
        if self.errors_on and self.in_motion:
            front += gauss(self.walk_error_mean, self.walk_error_variance)

        drift = self.drift
        if self.errors_on and self.in_motion:
            drift += gauss(self.drift_error_mean, self.drift_error_variance)

        self.rotate = (self.rotate + turn) % 360
        self.view_rot = (self.view_rot + turn) % 360

        self.x += cos(radians(self.rotate)) * front
        self.y -= sin(radians(self.rotate)) * front

        self.x -= sin(radians(self.rotate)) * drift
        self.y -= cos(radians(self.rotate)) * drift

        for line in lines:
            x, y = collision_robot_vs_line(self, line)
            self.x += x
            self.y += y

        for goal in goals:
            x, y = collision_robot_vs_goal(self, goal)
            self.x += x
            self.y += y

        for robot in robots:
            if robot.KEY != self.KEY:
                x, y = collision_robot_vs_robot(self, robot)
                self.x += x
                self.y += y

        collision_robot_vs_ball(self, self.ball)
        self.get_orientation()  # cumulative error

    def right_kick(self):
        R = degrees(atan2((self.y - self.ball.y), (self.ball.x - self.x)))
        d = sqrt((self.x - self.ball.x) ** 2 + (self.y - self.ball.y) ** 2)
        force = min(10,
                    12 * exp(-2.3 / self.ball.radius * d + 2.3 / self.ball.radius * (self.radius + self.ball.radius)))

        r = R
        if R < 0: r = R + 360

        if self.rotate < 30 and (r < self.rotate or r > 330 + self.rotate) or r < self.rotate and r > self.rotate - 30:
            if self.errors_on:
                self.ball.put_in_motion(force + gauss(self.kick_error_force_mean, self.kick_error_force_variance),
                                        self.rotate + gauss(self.kick_error_angle_mean, self.kick_error_angle_variance))
            else:
                self.ball.put_in_motion(force, self.rotate)

        self.control.action_select(0)

    def left_kick(self):
        R = degrees(atan2((self.y - self.ball.y), (self.ball.x - self.x)))
        d = sqrt((self.x - self.ball.x) ** 2 + (self.y - self.ball.y) ** 2)
        force = min(10,
                    12 * exp(-2.3 / self.ball.radius * d + 2.3 / self.ball.radius * (self.radius + self.ball.radius)))

        r = R
        if R < 0: r = R + 360

        if self.rotate > 330 and (r > self.rotate or r < self.rotate - 330) or r > self.rotate and r < self.rotate + 30:
            if self.errors_on:
                self.ball.put_in_motion(force + gauss(self.kick_error_force_mean, self.kick_error_force_variance),
                                        self.rotate + gauss(self.kick_error_angle_mean, self.kick_error_angle_variance))
            else:
                self.ball.put_in_motion(force, self.rotate)

        self.control.action_select(0)

    def get_orientation(self):
        if self.errors_on:
            self.orientation_error += gauss(self.imu_error_mean, self.imu_error_variance)
        return self.rotate + self.orientation_error

    def pass_left(self):
        R = degrees(atan2((self.y - self.ball.y), (self.ball.x - self.x)))
        d = sqrt((self.x - self.ball.x) ** 2 + (self.y - self.ball.y) ** 2)
        force = min(10,
                    12 * exp(-2.3 / self.ball.radius * d + 2.3 / self.ball.radius * (self.radius + self.ball.radius)))

        r = R
        if R < 0: r = R + 360

        if (self.rotate < 15 and (r < self.rotate + 15 or r > self.rotate + 345) or
                        self.rotate > 345 and (r > self.rotate - 15 or r < self.rotate - 345) or
                        r < self.rotate + 15 and r > self.rotate - 15):
            if self.errors_on:
                self.ball.put_in_motion(force + gauss(self.kick_error_force_mean, self.kick_error_force_variance),
                                        self.rotate + 90 + gauss(self.kick_error_angle_mean,
                                                                 self.kick_error_angle_variance))
            else:
                self.ball.put_in_motion(force, self.rotate + 90)

        self.control.action_select(0)

    def pass_right(self):
        R = degrees(atan2((self.y - self.ball.y), (self.ball.x - self.x)))
        d = sqrt((self.x - self.ball.x) ** 2 + (self.y - self.ball.y) ** 2)
        force = min(10,
                    12 * exp(-2.3 / self.ball.radius * d + 2.3 / self.ball.radius * (self.radius + self.ball.radius)))

        r = R
        if R < 0: r = R + 360

        if (self.rotate < 15 and (r < self.rotate + 15 or r > self.rotate + 345) or
                        self.rotate > 345 and (r > self.rotate - 15 or r < self.rotate - 345) or
                        r < self.rotate + 15 and r > self.rotate - 15):
            if self.errors_on:
                self.ball.put_in_motion(force + gauss(self.kick_error_force_mean, self.kick_error_force_variance),
                                        self.rotate - 90 + gauss(self.kick_error_angle_mean,
                                                                 self.kick_error_angle_variance))
            else:
                self.ball.put_in_motion(force, self.rotate - 90)

        self.control.action_select(0)


    '''Vision'''

    def toRectangular(self,point):
        r = point[0]
        a = point[1]
        return (r * cos(a), r * sin(a))


    def draw_vision(self,screen):
        #print '********************************************* ',self.view_rot
        vision_dist = self.vision_dist
        field_of_view = self.field_of_view
        startRad = radians(-35 + self.view_rot)
        endRad = radians(35 + self.view_rot)


        vision_surface = pygame.Surface((vision_dist * 2, vision_dist * 2))
        vision_surface.fill(screen.GREEN)
        vision_surface.set_colorkey(screen.GREEN)
        vision_surface.set_alpha(200)
        vision_surface_center = (vision_dist, vision_dist)


       # if self.view_rot < 0:
       #     self.view_rot = self.view % 360

        #if self.view_rot > (self.rotate + 90):
        #    self.view_rot = self.rotate + 90

        #elif self.view_rot < (self.rotate - 90):
        #    self.view_rot = self.rotate - 90


        theta_vision = radians(self.view_rot)

        angle_1 = -theta_vision + field_of_view/2
        angle_2 = -theta_vision - field_of_view/2

        point_1 = (vision_dist, angle_1)
        point_2 = (vision_dist, angle_2)

        point_1 = self.toRectangular(point_1)
        point_2 = self.toRectangular(point_2)

        point_1 = (point_1[0] + vision_surface_center[0], point_1[1] + vision_surface_center[1])
        point_2 = (point_2[0] + vision_surface_center[0], point_2[1] + vision_surface_center[1])


        pygame.draw.arc(screen.background, screen.WHITE,[self.x - vision_dist, self.y - vision_dist, vision_dist * 2, vision_dist * 2], startRad,endRad, 1)
        pygame.draw.arc(screen.background, screen.WHITE, [self.x - vision_dist/2, self.y - vision_dist/2, vision_dist, vision_dist], startRad, endRad, 1)

        pygame.draw.line(vision_surface, screen.WHITE, vision_surface_center, point_1, 1)
        pygame.draw.line(vision_surface, screen.WHITE, vision_surface_center, point_2, 1)


        position = (
            self.x - vision_dist,
            self.y - vision_dist
        )

        screen.background.blit(vision_surface, position)


    def ball_search(self,x,y):
        self.ball.view_obj(self.Mem, self.bkb,self.x,self.y,x,y,self.rotate,self.vision_dist)


    def perform_pan(self):
        if self.bkb.read_int(self.Mem,'VISION_SEARCH_BALL') == 1:
            self.view_rot = self.pan(self.view_rot,self.rotate)
            rot = self.view_obj(self.Mem,self.bkb,self.x,self.y,500,500,self.view_rot)
            if rot == 99999:
                self.bkb.write_int(self.Mem,'VISION_SEARCH_BALL',0)


    def searching(self):
        self.perform_pan()
        #self.perform_pan(self.ball.x,self.ball.y)
        #if self.robots:
        #    for i in range(0, len(self.robots)):
        #        self.robots[i].perform_pan(self.ball.x,self.ball.y)
        #        for j in range(0, len(self.robots)):
        #            if i!=j:
        #                self.robots[i].perform_pan(self.robots[j].x,self.robots[j].y)



    def vision_process(self,ballX,ballY,robots):
        #TODO alterei tambem por causa da decisao
        if (self.bkb.read_int(self.Mem,'DECISION_ACTION_VISION') == 0):
            #ball detect
            rotation_vision = self.ball_detect(self.Mem,self.bkb, self.view_rot, self.rotate, self.x, self.y, ballX,ballY)
            if (rotation_vision != None):
                #print 'rotat_raw',rotation_vision
                if rotation_vision > 90:
                    rotation_vision = 90
                elif rotation_vision < -90:
                    rotation_vision = -90
                self.view_rot = rotation_vision + self.rotate
                print 'self.rotate',self.rotate
                print 'rotation_vision',rotation_vision
                print 'view_rot', self.view_rot



            #robot detect
            if robots:
                for j in range(0, len(robots)):
                    if j!=self.index-1:
                        self.robot_detect(self.Mem,self.bkb, self.view_rot, self.rotate, self.x, self.y, robots[j].x, robots[j].y, j)