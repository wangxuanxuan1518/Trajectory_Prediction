import lanelet2
import math
import tempfile
import os
import numpy as np
import matplotlib.pyplot as plt
from lanelet2.core import AttributeMap,TrafficLight,Lanelet,LineString3d,Point2d,Point3d,LaneletMap,getId,BoundingBox2d,BasicPoint2d
from lanelet2.projection import UtmProjector
file_path = "Amsterdamer_Intersection_Lanelet.osm"


def find_lane(xf,yf,x,y):
    projector = UtmProjector(lanelet2.io.Origin(50.76599713889, 6.06099834167))
    path = file_path
    map = lanelet2.io.load(path, projector)

    p_init = Point3d(getId(),x,y,0)

    #first step,find the area the point belongs to
    Lane = []
    for lane in map.laneletLayer:
        left  = lane.leftBound
        right = lane.rightBound
        #distinguish between right-turn and left-turn lane,these two types have different computation geometry
        xa = left[1].x - left[0].x
        ya = left[1].y - left[0].y
        xb = ya
        yb = -xa
        xc = left[-1].x - left[-2].x
        yc = left[-1].y - left[-2].y
        pro = (xb * xc + yb *yc)/ (math.sqrt(xb**2 + yb**2) * math.sqrt(xc**2 + yc**2))

        if pro < -0.6:
            # left-turn lane
            left_inv = left.invert()
            a = 1
            int = 0

            ab_init = np.array([right[1].x - right[0].x, right[1].y - right[0].y])
            ac_init = np.array([p_init.x - right[0].x, p_init.y - right[0].y])
            c_init = np.cross(ab_init, ac_init)
            c = c_init

            for i in range(1, len(right) - 1):
                ab = np.array([right[i + 1].x - right[i].x, right[i + 1].y - right[i].y])
                ac = np.array([p_init.x - right[i].x, p_init.y - right[i].y])
                cd = np.cross(ab, ac)
                if cd * c < 0:
                    a = 0
                c = cd

            ab = np.array([left_inv[0].x - right[-1].x, left_inv[0].y - right[-1].y])
            ac = np.array([p_init.x - right[-1].x, p_init.y - right[-1].y])
            cd = np.cross(ab, ac)
            if cd * c < 0:
                a = 0
            c = cd

            for i in range(len(left_inv) - 1):
                ab = np.array([left_inv[i + 1].x - left_inv[i].x, left_inv[i + 1].y - left_inv[i].y])
                ac = np.array([p_init.x - left_inv[i].x, p_init.y - left_inv[i].y])
                cd = np.cross(ab, ac)
                if cd * c > 0:
                    int = 1

            ab = np.array([right[0].x - left_inv[-1].x, right[0].y - left_inv[-1].y])
            ac = np.array([p_init.x - left_inv[-1].x, p_init.y - left_inv[-1].y])
            cd = np.cross(ab, ac)
            if cd * c < 0:
                a = 0

            if a == 1 and int == 1:
                Lane.append(lane)

        else:
            #right turn and go straight
            right_inv = right.invert()
            a = 1
            int = 0

            ab_init = np.array([left[1].x - left[0].x, left[1].y - left[0].y])
            ac_init = np.array([p_init.x - left[0].x, p_init.y - left[0].y])
            c_init = np.cross(ab_init,ac_init)
            c = c_init

            for i in range(1,len(left)-1):
                ab = np.array([left[i+1].x - left[i].x,left[i+1].y - left[i].y])
                ac = np.array([p_init.x - left[i].x, p_init.y - left[i].y ])
                cd = np.cross(ab,ac)
                if cd*c < 0:
                   a = 0
                c = cd

            ab = np.array([right_inv[0].x - left[-1].x,right_inv[0].y - left[-1].y])
            ac = np.array([p_init.x - left[-1].x, p_init.y - left[-1].y ])
            cd = np.cross(ab, ac)
            if cd * c < 0:
                 a = 0
            c = cd

            for i in range(len(right_inv)-1):
                ab = np.array([right_inv[i+1].x - right_inv[i].x,right_inv[i+1].y - right_inv[i].y])
                ac = np.array([p_init.x - right_inv[i].x, p_init.y - right_inv[i].y ])
                cd = np.cross(ab,ac)
                if cd*c > 0:
                     int = 1

            ab = np.array([left[0].x - right_inv[-1].x, left[0].y - right_inv[-1].y])
            ac = np.array([p_init.x - right_inv[-1].x, p_init.y - right_inv[-1].y])
            cd = np.cross(ab, ac)
            if cd * c < 0:
                 a = 0

            if a == 1 and int==1 :
                Lane.append(lane)

    #second step,sometimes a point belongs to different lanes,we need to find the only one correct lane.
    vx = x - xf
    vy = y - yf
    cos_max = -1
    #here we will use the vector of velocity. In our neural network, the position of the last time step will be used.
    if len(Lane)==1:
        # there is only one lane,especially in the area before the intersection
        lan = Lane[0]
    else:
        for lane in Lane:
            Stringline_left = lane.leftBound
            vecx = Stringline_left[-1].x - Stringline_left[0].x
            vecy = Stringline_left[-1].y - Stringline_left[0].y
            cos_t = (vecx * vx + vecy *vy)/ (math.sqrt(vecx**2 + vecy**2) * math.sqrt(vx**2 + vy**2))
            if cos_t > cos_max:
                cos_max = cos_t
                lan = lane
    return lan



def Krumung_rechnen(laneLET):
    string_a = laneLET.leftBound
    string_b = laneLET.rightBound
    #krummung left Bound
    k1 = (string_a[-1].y - string_a[-2].y) / (string_a[-1].x - string_a[-2].x)
    k1_1 = -1 / k1
    x1 = (string_a[-1].x + string_a[-2].x) / 2
    y1 = (string_a[-1].y + string_a[-2].y) / 2

    k2 = (string_a[1].y - string_a[0].y) / (string_a[1].x - string_a[0].x)
    k2_1 = -1 / k2
    x2 = (string_a[1].x + string_a[0].x) / 2
    y2 = (string_a[1].y + string_a[0].y) / 2

    if (k2_1 - k1_1)==0:
        r1 = 1000
    else:
        x_1 = (k1_1 * x1 - k2_1 * x2 - y1 + y2) / (k1_1 - k2_1)
        y_1 = (-k2_1 * k1_1 * x1 + y1 * k2_1 + k1_1 * k2_1 * x2 - k1_1 * y2) / (k2_1 - k1_1)
        r1 = (math.sqrt((x_1 - x1) ** 2 + (y_1 - y1) ** 2) + math.sqrt((x_1 - x2) ** 2 + (y_1 - y2) ** 2))/2
    #krummung right Bound
    k1 = (string_b[-1].y - string_b[-2].y) / (string_b[-1].x - string_b[-2].x)
    k1_1 = -1 / k1
    x1 = (string_b[-1].x + string_b[-2].x) / 2
    y1 = (string_b[-1].y + string_b[-2].y) / 2

    k2 = (string_b[1].y - string_b[0].y) / (string_b[1].x - string_b[0].x)
    k2_1 = -1 / k2
    x2 = (string_b[1].x + string_b[0].x) / 2
    y2 = (string_b[1].y + string_b[0].y) / 2

    if (k2_1 - k1_1)==0:
        r2 = 1000
    else:
        x_1 = (k1_1 * x1 - k2_1 * x2 - y1 + y2) / (k1_1 - k2_1)
        y_1 = (-k2_1 * k1_1 * x1 + y1 * k2_1 + k1_1 * k2_1 * x2 - k1_1 * y2) / (k2_1 - k1_1)
        r2 = (math.sqrt((x_1 - x1) ** 2 + (y_1 - y1) ** 2) + math.sqrt((x_1 - x2) ** 2 + (y_1 - y2) ** 2)) / 2

    R = (r1 + r2)/2
    return R


if __name__ == '__main__':
    lane = find_lane(45,6,40,7)
    # in the recurrent neural network,this data will be pos_x[i],pos_y[i]
    # because of the noise, the first two data may choose pos_x[i-3],pos_y[i-3]
    print(lane)
    print(Krumung_rechnen(lane))









