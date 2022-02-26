#!/usr/binenv python
# -*- coding: utf-8 -*-
#文档地址  http://los-cocos.github.io/cocos-site/doc/programming_guide/index.html
from __future__ import print_function, division
import random

from cocos.director import director
from cocos.scene import Scene
from cocos.scenes import *
from cocos.layer import ColorLayer
from cocos.sprite import Sprite
from cocos.text import Label
from cocos.actions import *

import cocos.euclid as eu
import cocos.collision_model as cm
from pygments import highlight
from sqlalchemy import false


class LaunchLayer(ColorLayer):
    """
    开场动画图层
    """
    is_event_handler = True

    def __init__(self):
        super(LaunchLayer, self).__init__(222, 200, 158, 255)
        sprite = Sprite('hanoi.png')  # 创建一个显示矩形图像的部件
        w, h = director.get_window_size()  # 获取当前窗口的大小
        sprite.position = w / 2 - 10, 380  # 设置图像位置

        plate1 = Sprite('plate.jpeg', position=(w / 2 - 10, 130))  # 创建一个 盘子 图片部件，并设置位置为x，x
        plate2 = Sprite('plate.jpeg', position=(w / 2 - 10, 195))  # 创建一个 盘子 图片部件，并设置位置为x，x
        plate3 = Sprite('plate.jpeg', position=(w / 2 - 10, 265))  # 创建一个 盘子 图片部件，并设置位置为x，x
        self.add(sprite)  #添加一个子对象，如果它成为活动场景的一部分，调用 on_enter 函数

        plate2.scale_x = 0.8  # 盘子图片 设置x方向缩放倍数 x
        plate3.scale_x = 0.6  # 盘子图片 设置x方向缩放倍数 x
        self.add(plate1)  # 添加 盘子图片 进入活动场景
        self.add(plate2)  # 添加 盘子图片 进入活动场景
        self.add(plate3)  # 添加 盘子图片 进入活动场景

        # 刚开始的可见度都为0
        sprite.opacity = 0  # 先全部隐藏 做动画
        plate3.opacity = 0  # 先全部隐藏 做动画
        plate2.opacity = 0  # 先全部隐藏 做动画
        plate1.opacity = 0  # 先全部隐藏 做动画

        plate1.do(AccelDeccel(FadeIn(1.5) | MoveBy((0, -30), duration=1.5)))  # 1.5s内进行位置和透明度的匀速变换
        plate2.do(AccelDeccel(Delay(0.3) + FadeIn(0.3) | MoveBy((0, -30), duration=0.3)))  # 先延时1s 共 2.5s内进行位置和透明度的匀速变换
        plate3.do(AccelDeccel(Delay(0.6) + FadeIn(0.3) | MoveBy((0, -30), duration=0.6)))  # 先延时2s 共 3.5s内进行位置和透明度的匀速变换

        sprite.do(AccelDeccel(Delay(1) + FadeIn(0.3) | MoveBy((0, -30), duration=1.3)))  # 先延时3s 共 4.5s内进行位置和透明度的匀速变换

        # 这里设置在4秒之后自动开始游戏
        self.schedule_interval(self.start_game, 2)  # 定时4s进入回调函数 start_game

    def on_key_press(self, k, m):
        self.start_game(None)

    # 开始游戏的方法
    def start_game(self, dt):
        director.replace(FadeTransition(Scene(GameLayer(level=1)), duration=1))
        # 1s内 将活动场景替换为新场景。活动场景结束(淡出传出场景，然后淡入传入场景 (新建一个游戏类的场景，等级 为1级) )


class Actor(Sprite):
    """
    游戏中的元素基类 基于类 Sprite
    """
    def __init__(self, position=(0, 0), rotation=0, scale=1, *args, **kwargs):
        """构造器

        Args:
            position (tuple, optional): 位置. Defaults to (0, 0).
            rotation (int, optional): 旋转. Defaults to 0.
            scale (int, optional): 整体缩放. Defaults to 1.
        """
        # 初始化的是盘子的图片?哦，盘子竖起来是元胞，我人傻了
        super(Actor, self).__init__('six3.png', position, rotation, scale)
        # 这是线性代数?
        self.position = eu.Vector2(position[0], position[1])
        if 'scale_x' in kwargs:
            self.scale_x = kwargs['scale_x']  # 比例尺,x轴缩放
        if 'scale_y' in kwargs:
            self.scale_y = kwargs['scale_y']  # 比例尺,x轴缩放
        self.cshape = cm.AARectShape(self.position, self.width * scale * 6, self.height * scale * 6)


class Cell(Actor):
    """
    细胞
    """
    def __init__(self, position=(0, 0), num=9999, live=False, scale=1, *args, **kwargs):
        # 初始化一个垂直的盘子图像,变为元胞 90度
        super(Cell, self).__init__(position=position, rotation=0, scale=0.1, *args, **kwargs)
        self.num = num
        self.live = live
        # 盘子已栈结构存储
        # 每个元胞都有一个盘子栈


# 继承父类ColorLayer
class GameLayer(ColorLayer):
    # 全局变量
    is_event_handler = True  # 是否为时间处理者？

    GameW = 50  # 50 宽度
    GameH = 26  # 25 高度
    Scale = 1.0  # 1.0 缩放比例
    RuleBirth = 2  # 出生规则 出生需要几个活着的细胞
    RuleLive = 2,3  # 存活规则 存活需要几个活着的细胞
    RandomNum = 600 # 随机生成存活数量
    probability = 3 # 生成几率

    def __init__(self, level=3):
        super(GameLayer, self).__init__(0, 0, 0, 255)  # 使用父类的构造器 背景颜色
        self.cells = []
        k = 0
        for i in range(self.GameW):
            for j in range(self.GameH * 2):
                if ((i + j) % 2 == 0):
                    cell = Cell(position=((i * 17 * self.Scale) + 9, (j * 10 * self.Scale) + 9), num=k, live=False, scale=self.Scale)  # 初始化元胞对象 并设置初始位置
                    k = k + 1
                    self.cells.append(cell)
        self.cell1 = Cell(position=(160, 200))  # 初始化元胞对象 并设置初始位置
        w, h = director.get_window_size()
        self.collman = cm.CollisionManagerGrid(0, w, 0, h, self.cell1.width * 1.25, self.cell1.height * 1.25)
        for i in range(len(self.cells)):
            self.add(self.cells[i])  # 添加元胞进入活动场景
            self.collman.add(self.cells[i])  # 根据碰撞体积点增加对象
            self.cells[i].do(Hide())

        # 初始化重置按钮对象(图片，背景，大小缩放)
        self.restart = Sprite('refresh.png', color=(255, 255, 255), scale=0.2)
        # 设置重置按钮对象位置
        self.restart.position = 40, 565
        self.restart.cshape = cm.AARectShape(self.restart.position, self.restart.width * 0.2 * 0.5, self.restart.height * 0.2 * 0.5)
        self.add(self.restart)

        self.clearbutton = Sprite('refresh.png', color=(255, 255, 255), scale=0.2)
        # 设置重置按钮对象位置
        self.clearbutton.position = 90, 565
        self.clearbutton.cshape = cm.AARectShape(self.clearbutton.position, self.clearbutton.width * 0.2 * 0.5, self.clearbutton.height * 0.2 * 0.5)
        self.add(self.clearbutton)

        # # 目前只监听step的更新
        self.schedule(self.update)

        self.Randombutton = Sprite('refresh.png', color=(255, 255, 255), scale=0.2)
        # 设置重置按钮对象位置
        self.Randombutton.position = 140, 565
        self.Randombutton.cshape = cm.AARectShape(self.Randombutton.position, self.Randombutton.width * 0.2 * 0.5, self.Randombutton.height * 0.2 * 0.5)
        self.add(self.Randombutton)

        # # 目前只监听step的更新
        self.schedule(self.update)

    startgame = 0

    def update(self, dt):
        thisStatu = []
        if (self.startgame == 1):
            # self.st.element.text = 'Steps: ' + str(self.step)
            print("update")
            for i in range(self.GameH * self.GameW):
                thisStatu.append(self.up(i))
            for j in range(len(thisStatu)):
                self.cellIslive(self.cells[j], thisStatu[j])
        # self.startgame = 0

    # def server(self):
    def up(self, xx):
        lnf = self.calfun(xx, self.GameH)
        life = 0
        for i in lnf:
            i = i % (self.GameH * (self.GameW))
            if (self.cells[i].live == True):
                life = life + 1
        if (life == self.RuleBirth and self.cells[xx].live == False):  # 出生
            ret = True
        elif (life in self.RuleLive and self.cells[xx].live == True):  # 存活
            ret = True
        else:
            ret = False
        # print("  "+str(life))
        return ret

    def start(self):
        self.startgame = not self.startgame

    def clear(self):
        k = 0
        for i in range(self.GameW):
            for j in range(self.GameH * 2):
                if ((i + j) % 2 == 0):
                    self.cellIslive(self.cells[k], False)
                    k = k + 1
        self.startgame = 0
    def random(self):
        k = 0
        b=0
        for i in range(self.GameW):
            for j in range(self.GameH * 2):
                if ((i + j) % 2 == 0):
                    live = False
                    a=random.randint(0,self.probability)
                    if a == 0:
                        live = True
                        b=b+1
                    else:
                        live = False
                        
                    self.cellIslive(self.cells[k], live)
                    k = k + 1
                    if(b>self.RandomNum):
                        break
        self.startgame = 0

    # 没有找到调用的地方，请查看文档 http://los-cocos.github.io/cocos-site/doc/programming_guide/quickstart.html#handling-events
    def on_mouse_press(self, x, y, k, m):
        if self.restart.cshape.touches_point(x, y):  # 判断鼠标是不是点击了 重置按钮的碰撞对象
            self.start()  # 初始化当前等级
        if self.clearbutton.cshape.touches_point(x, y):  # 判断鼠标是不是点击了 重置按钮的碰撞对象
            self.clear()  # 初始化当前等级
        if self.Randombutton.cshape.touches_point(x, y):  # 判断鼠标是不是点击了 重置按钮的碰撞对象
            self.random()  # 初始化当前等级
        # 判断是否点击重来
        # sprite.
        # 找到鼠标拖动的盘子
        for cell in self.cells:
            # 只能点击栈顶的盘子
            if cell.cshape.touches_point(x, y):
                # 只能点击栈顶的盘子
                print(cell.num)
                cell.live = not cell.live
                if (cell.live == False):
                    cell.do(Hide())
                else:
                    cell.do(Show())

    def calfun(self, x, h):
        if ((x // h) % 2 == 0):
            return x + 1, x - 1, x - h, x - h - 1, x + h, x + h - 1
        elif ((x // h) % 2 == 1):
            return x + 1, x - 1, x - h, x - h + 1, x + h, x + h + 1

    def cellIslive(self, cell, live):
        if live == True:
            cell.do(Show())
        else:
            cell.do(Hide())
        cell.live = live

    def on_mouse_drag(self, x, y, dx, dy, k, m):
        for cell in self.cells:
            # 只能点击栈顶的盘子
            if cell.cshape.touches_point(x, y):
                print(cell.num)
                cell.live = True
                cell.do(Show())


if __name__ == '__main__':
    director.init(caption='Hanoi by anosann', width=860,height=590)  # 初始化导演
    director.run(Scene(LaunchLayer()))  # 导演执行初始场景
