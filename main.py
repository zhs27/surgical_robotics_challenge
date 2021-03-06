#!/usr/bin/env python
# //==============================================================================
# /*
#     Software License Agreement (BSD License)
#     Copyright (c) 2020-2021 Johns Hopkins University (JHU), Worcester Polytechnic Institute (WPI) All Rights Reserved.


#     All rights reserved.

#     Redistribution and use in source and binary forms, with or without
#     modification, are permitted provided that the following conditions
#     are met:

#     * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.

#     * Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.

#     * Neither the name of authors nor the names of its contributors may
#     be used to endorse or promote products derived from this software
#     without specific prior written permission.

#     THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#     "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#     LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#     FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#     COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#     INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#     BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#     LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#     CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#     LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#     ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#     POSSIBILITY OF SUCH DAMAGE.


#     \author    <amunawar@jhu.edu>
#     \author    Adnan Munawar
#     \version   1.0
# */
# //==============================================================================
from surgical_robotics_challenge.kinematics.psmIK import *
from ambf_client import Client
from surgical_robotics_challenge.psm_arm import PSM
import time
import rospy
from PyKDL import Frame, Rotation, Vector
from argparse import ArgumentParser
from surgical_robotics_challenge.utils.obj_control_gui import ObjectGUI
from surgical_robotics_challenge.utils.jnt_control_gui import JointGUI
from surgical_robotics_challenge.ecm_arm import ECM
from surgical_robotics_challenge.utils.utilities import get_boolean_from_opt

class PSMController:
    #def __init__(self, gui_handle, arm):
    def __init__(self,  arm):
        self.counter = 0
        #self.GUI = gui_handle
        self.arm = arm

    def update_arm_pose(self, x, y, z, ro, pi, ya, gr):
    #def update_arm_pose(self):
        #gui = self.GUI
        #gui.App.update()
        T_t_b = Frame(Rotation.RPY(ro, pi, ya), Vector(x, y, z))
		#T_t_b = Frame(Rotation.RPY(gui.ro, gui.pi, gui.ya), Vector(gui.x, gui.y, gui.z))
        self.arm.servo_cp(T_t_b)
        self.arm.set_jaw_angle(gr)
        self.arm.run_grasp_logic(gr)
        #self.arm.set_jaw_angle(gui.gr)
        #self.arm.run_grasp_logic(gui.gr)

    #def update_visual_markers(self):
    def update_visual_markers(self, x, y, z, ro, pi, ya, gr):
        # Move the Target Position Based on the GUI
        if self.arm.target_IK is not None:
            gui = self.GUI
            #T_ik_w = self.arm.get_T_b_w() * Frame(Rotation.RPY(gui.ro, gui.pi, gui.ya), Vector(gui.x, gui.y, gui.z))
	    T_ik_w = self.arm.get_T_b_w() * Frame(Rotation.RPY(ro, pi, ya), Vector(x, y, z))
            self.arm.target_IK.set_pos(T_ik_w.p[0], T_ik_w.p[1], T_ik_w.p[2])
            self.arm.target_IK.set_rpy(T_ik_w.M.GetRPY()[0], T_ik_w.M.GetRPY()[1], T_ik_w.M.GetRPY()[2])
        if self.arm.target_FK is not None:
            ik_solution = self.arm.get_ik_solution()
            ik_solution = np.append(ik_solution, 0)
            T_t_b = convert_mat_to_frame(compute_FK(ik_solution))
            T_t_w = self.arm.get_T_b_w() * T_t_b
            self.arm.target_FK.set_pos(T_t_w.p[0], T_t_w.p[1], T_t_w.p[2])
            self.arm.target_FK.set_rpy(T_t_w.M.GetRPY()[0], T_t_w.M.GetRPY()[1], T_t_w.M.GetRPY()[2])

    def run(self, x, y, z, ro, pi, ya, gr):
        #self.update_arm_pose()
        #self.update_arm_pose(-0.268657, -0.100746, -1.167910, 1.841493, 0, 0.630491, 0.5)
        self.update_arm_pose(x, y, z, ro, pi, ya, gr)
        #self.update_arm_pose(-0.268657, -0.100746, -1.167910, 1.841493, 0, 0.630491, 0.5)
        #self.update_visual_markers()
        self.update_visual_markers(x, y, z, ro, pi, ya, gr)



class ECMController:
    def __init__(self, gui, ecm):
        self.counter = 0
        self._ecm = ecm
        self._cam_gui = gui

    def update_camera_pose(self):
        self._cam_gui.App.update()
        self._ecm.servo_jp(self._cam_gui.jnt_cmds)

    def run(self):
            self.update_camera_pose()


def interpolate(x1,y1,z1, x2, y2, z2, r1, p1, yaw1, r2, p2, yaw2, gr, n, controller):
	deltax = (x2 - x1) / n
	deltay = (y2 - y1) / n
	deltaz = (z2 - z1) / n
        deltar = (r2 - r1) / n
	deltap = (p2 - p1) / n
	deltayaw = (yaw2 - yaw1) / n
	for i in range(n):
		x1 += deltax
		y1 += deltay
		z1 += deltaz
		r1 += deltar
		p1 += deltap
		yaw1 += deltayaw
		controller.run(x1, y1, z1, r1, p1, yaw1, gr)
		
		
		


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-c', action='store', dest='client_name', help='Client Name', default='ambf_client')
    parser.add_argument('--one', action='store', dest='run_psm_one', help='Control PSM1', default=True)
    parser.add_argument('--two', action='store', dest='run_psm_two', help='Control PSM2', default=True)
    parser.add_argument('--three', action='store', dest='run_psm_three', help='Control PSM3', default=False)
    parser.add_argument('--ecm', action='store', dest='run_ecm', help='Control ECM', default=True)

    parsed_args = parser.parse_args()
    print('Specified Arguments')
    print(parsed_args)
    

    parsed_args.run_psm_one = get_boolean_from_opt(parsed_args.run_psm_one)
    parsed_args.run_psm_two = get_boolean_from_opt(parsed_args.run_psm_two)
    parsed_args.run_psm_three = get_boolean_from_opt(parsed_args.run_psm_three)
    parsed_args.run_ecm = get_boolean_from_opt(parsed_args.run_ecm)

    c = Client(parsed_args.client_name)
    c.connect()
    
    #c1 = Client(parsed_args.client_name)
    #c1.connect()

    time.sleep(0.5)
    controllers = []
    psm = PSM(c, 'psm2')
    psm1 = PSM(c, 'psm1')
    controller1 = PSMController(psm1)
    controller = PSMController(psm)
    
    x = 0.593284
    y = 0.078358
    z = -1.156716
    r = 3.14
    p = 0
    yaw = 1.570790
    interpolate(0, 0, -1, x, 0.078358, z, r, p, yaw, r, p, yaw, 0.0, 1000, controller1)

    x = 0.0
    for i in range(1000):
	    x -= 0.38657 / 1000
	    controller.run(x, 0.0, -1.0, 1.841493, 0, 0.630491, 0.5)
	    
    y = 0.0
    for i in range(1000):
        y += 0.1 / 1000
        controller.run(x, y, -1.0, 1.841493, 0, 0.630491, 0.5)
        
    z = -1.0
    for i in range(1000):
        z -= 0.167910 / 1000
        controller.run(x, y, z, 1.841493, 0, 0.630491, 0.5)
        
    for i in range(1000):
        y -= 0.154328 / 1000
        controller.run(x, y, z, 1.841493, 0, 0.630491, 0.5)

    for i in range(1000):
        x += 0.05 / 1000
        controller.run(x, y, z, 1.841493, 0, 0.630491, 0.5)
    
    deltay = (-0.18 - y) / 1000
    for i in range(1000):
        y += deltay
        controller.run(x, y, z, 1.841493, 0, 0.630491, 0.5)
    deltax = (-0.21 - x) / 1000
    for i in range(1000):
        x += deltax
        controller.run(x, y, z, 1.841493, 0, 0.630491, 0.5)		
    #x = -0.26
    #controller.run(x, y, z, 1.841493, 0, 0.630491, 0.5)
    #x = -0.23
    #controller.run(x, y, z, 1.841493, 0, 0.630491, 0.5)
    #x = -0.21
    #controller.run(x, y, z, 1.841493, 0, 0.630491, 0.5)
    #controller.run(x, y, z, 1.841493, 0, 0.630491, 0.0)
    time.sleep(5)
    interpolate(x, y, z, -0.515, 0.17, -1.325, 1.841493, 0, 0.630491, 2.513134, -0.268657, 1.884223, 0.0, 1000, controller)
    x = -0.515
    y = 0.17
    z = -1.325
    r = 2.513134
    p = -0.268657
    yaw = 1.884223
    time.sleep(1)
    interpolate(x, y, z, -0.515, 0.17, -1.35, 1.841493, 0, 0.630491, 2.513134, -0.268657, 1.0, 0.0, 1000, controller)
    
    x = 0.593284
    y = 0.078358
    z = -1.156716
    r = 3.14
    p = 0
    yaw = 1.570790   
    x1 = 0.526119
    y1 = 0.055970
    z1 = -1.1369403
    r = 3.14
    p = 0
    yaw = 1.570790

    interpolate(x,y,z, x1, y1, z1, r, p, yaw, r, p, yaw, 0.0, 1000, controller1)
    x = 0.500896
    y = 0.043970
    z = -1.38895
    interpolate(x1,y1,z1, x, y, z, r, p, yaw, r, p, yaw, 0.5, 1000, controller1)
    controller1.run(x, y, z, r, p, yaw, 0.0)
    time.sleep(2)
    controller.run(-0.515, 0.17, -1.35, 2.513134, -0.268657, 1.0, 0.5)
    
    x1 = 0.12
    y1 = 0.053970
    z1 = -1.378209
    interpolate(x,y,z, x1, y1, z1, r, p, yaw, r, p, 1.99, 0.0, 1000, controller1)
    time.sleep(2)
    x1 = -0.503731
    y1 = -0.044776
    z1 = -1.190299
    interpolate(-0.515, 0.17, -1.35, x1, y1, z1, 2.513134, -0.268657, 1.0, 2.513134, -0.268657, 1.0, 0.5, 1000, controller)
    x = -0.540896
    y = -0.011194
    z = -1.4365675
    r = 3.319104
    p = -0.223881
    yaw = 0.496163
    controller.run(x1, y1, z1, r,p, yaw, 0.5)

    interpolate(x1, y1, z1, x, y, z, r, p, yaw, r, p, yaw, 0.5, 1000, controller)
    controller.run(x, y, z, r,p, yaw, 0.0)
    controller1.run(0.5589, 0.073970, -1.238209, 3.14 , 0, 1.570790, 0.5)
    interpolate(0.55896, 0.073970, -1.238209, 0, 0, -1, 3.14 , 0, 1.570790, 3.14 , 0, 1.570790, 0.5, 100, controller1)
    x1 = -0.694030
    y1 = y
    z1 = z
    interpolate(x, y, z, x1, y1, z1, r, p, yaw, r, p, yaw, 0.0, 1000, controller)
    x = -0.895522
    y = 0.167910
    z = -1.347015
    interpolate(x1, y1, z1, x, y, z, r, p, yaw, 2.513134, -0.268657, 1.884223, 0, 1000, controller)
    interpolate(x, y, z, -0.5, y, z, 2.513134, -0.268657, 1.884223, 2.513134, -0.268657, 1.884223, 0, 1000, controller)

    
    x1 = -0.2525
    y1 = 0.175
    z1 = -1.55
    interpolate(-0.5, y, z, x1, y1, z1, 2.513134, -0.268657, 1.884223, 2.513134, -0.268657, 1.884223, 0.0, 1000, controller) 
    x = -0.4515
    y = 0.149
    z = -1.5755
    time.sleep(1)
    interpolate(-0.5, y1, z1, x, y, z, r, p, yaw, 2.513134, -0.268657, 1.884223, 0.0, 1000, controller)
    
    
    x = 0.537313
    y = 0.223881
    z = -1.537313
    
    interpolate(0, 0, -1, x, y, z, 3.14 , 0, 1.570790, 3.14 , 0, 1.570790, 0.5, 1000, controller1)
    
    x1 = 0.537313
    y1 = 0.213881
    z1 = -1.560896
    interpolate(x, y, z, x1, y1, z1, 3.14 , 0, 1.570790, 3.14 , 0, 1.270790, 0.5, 1000, controller1)
    time.sleep(5)
    controller1.run(x1, y1, z1,3.14 , 0, 1.970790,0.0)
    time.sleep(5)
    controller.run(-0.4515, 0.149, -1.5755, 2.513134, -0.268657, 1.884223, 0.5)
    interpolate(-0.4515, 0.149, -1.5755, -0.4515, 0.149, -1.37, 2.513134, -0.268657, 1.884223, 2.513134, -0.268657, 1.884223, 0.5, 1000, controller)
    
    x = 0.407313
    y = 0.233881
    z = -1.350896

    interpolate(x1, y1, z1, x, y, z, 3.14 , 0, 1.570790, 3.14 , 0, 1.570790, 0.0, 1000, controller1)




    
    time.sleep(1000)
    
    


'''
    if parsed_args.run_psm_one is True:
        arm_name = 'psm1'
        psm = PSM(c, arm_name)
        if psm.base is not None:
            print('LOADING CONTROLLER FOR ', arm_name)
            # Initial Target Offset for PSM1
            # init_xyz = [0.1, -0.85, -0.15]
            init_xyz = [0, 0, -1.0]
            init_rpy = [3.14, 0, 1.57079]
            gui = ObjectGUI(arm_name + '/baselink', init_xyz, init_rpy, 3.0, 10.0, 0.000001)
            controller = PSMController(gui, psm)
            controllers.append(controller)

    if parsed_args.run_psm_two is True:
        arm_name = 'psm2'
        psm = PSM(c, arm_name)
        if psm.base is not None:
            print('LOADING CONTROLLER FOR ', arm_name)
            # Initial Target Offset for PSM2
            init_xyz = [0, 0.0, -1.0]
            init_rpy = [3.14, 0, 1.57079]
            gui = ObjectGUI(arm_name + '/baselink', init_xyz, init_rpy, 3.0, 12, 0.000001)
            controller = PSMController(gui, psm)
            controllers.append(controller)

    if parsed_args.run_psm_three is True:
        arm_name = 'psm3'
        psm = PSM(c, arm_name)
        if psm.base is not None:
            print('LOADING CONTROLLER FOR ', arm_name)
            # Initial Target Offset for PSM2
            init_xyz = [0, 0.0, -1.0]
            init_rpy = [3.14, 0, 1.57079]
            gui = ObjectGUI(arm_name + '/baselink', init_xyz, init_rpy, 3.0, 3.14, 0.000001)
            controller = PSMController(gui, psm)
            controllers.append(controller)

    if parsed_args.run_ecm is True:
        arm_name = 'CameraFrame'
        ecm = ECM(c, arm_name)
        gui = JointGUI('ECM JP', 4, ["ecm j0", "ecm j1", "ecm j2", "ecm j3"])
        controller = ECMController(gui, ecm)
        controllers.append(controller)

    if len(controllers) == 0:
        print('No Valid PSM Arms Specified')
        print('Exiting')

    else:
        while not rospy.is_shutdown():
            for cont in controllers:
                cont.run()
            time.sleep(0.005)
'''
