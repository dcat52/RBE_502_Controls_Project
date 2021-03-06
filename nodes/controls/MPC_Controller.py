# Linear MPC controller
#
#This controller was developed by Boyu Du, Hanshen Yu, and Siyu Li in 2018.
#
from cvxopt import matrix
from cvxopt.solvers import qp
import numpy as np
from math import cos, sin

def MPC_controller(controller, data):
    
    desired_x = data.desired_x
    desired_y = data.desired_y
    desired_x_dot = data.desired_x_dot
    desired_y_dot = data.desired_y_dot
    current_state_x = data.current_state_x
    current_state_y = data.current_state_y
    current_state_yaw = data.current_theta

    # def const params
    N = 5 #window length, larger = converge slower, less overshoot
    Q = [1, 1, 0.5] #gain for x, y, theta
    R = [0.1, 0.1] #dampening
    dt = data.time_step #time step
    #dt = 0.01
    x = current_state_x
    y = current_state_y
    t = current_state_yaw

    # create empty params
    x_r =np.zeros(N)# desired x, y, theta, v
    y_r =np.zeros(N)
    t_r =np.zeros(N)
    v_r =np.zeros(N)
    dx_r =np.zeros(N)# desired x_dot, y_dot, theta_dot
    dy_r =np.zeros(N)
    dt_r =np.zeros(N)
    A = np.zeros((3,3,N))# controller params
    B = np.zeros((3,2,N))

    # calc controller consts
    Q_hat = np.diag(np.tile(Q,N))
    R_hat = np.diag(np.tile(R,N))

    # calc ref params as model
    for i in range (0,N-1):
        x_r[i] = desired_x + dt * desired_x_dot * i
        y_r[i] = desired_y + dt * desired_y_dot * i
        dx_r[i] = desired_x_dot
        dy_r[i] = desired_y_dot
        t_r[i] = np.arctan2(dy_r[i],dx_r[i])
        dt_r[i] = 0
        v_r[i] = np.sqrt(dx_r[i]**2 + dy_r[i]**2)

    # update A and B mat for window
    for i in range (0,N-1):
        A[:,:,i] = [[1, 0, -v_r[i] * np.sin(t_r[i] * dt)],\
            [0, 1, v_r[i] * np.cos(t_r[i] * dt)],\
            [0, 0, 1]]
        B[:,:,i] = [[np.cos(t_r[i] * dt), 0],\
            [np.sin(t_r[i] * dt), 0],\
            [0, dt]]

    # calc new A_hat(3N,3), B_hat(3N,2N)
    A_hat = np.tile(np.eye(3,3),(N,1))
    B_hat = np.tile(np.zeros((3,2)),(N,N))
    for i in range(0,N-1):
        B_hat[i*3:, i*2:i*2+2] = np.tile(B[:,:,i],(N-i,1)) 
        for j in range(i,N-1):
            A_hat[j*3:j*3+3, :] = np.dot(A[:,:,i], A_hat[j*3:j*3+3,:])
            for m in range(i+1,j):
                B_hat[j*3:j*3+3, i*2:i*2+2] = np.dot(A[:,:,m], B_hat[j*3:j*3+3, i*2:i*2+2])

    # optimization
    e_hat = [[x - x_r[0],],[y - y_r[0]],[t - t_r[0]]]
    BQ_hat = np.dot(np.transpose(B_hat), Q_hat)
    qp_G = matrix(2*(np.dot(BQ_hat, B_hat) + R_hat))
    qp_a = matrix(2*(np.dot(np.dot(BQ_hat, A_hat), e_hat)))
    sol = qp(qp_G, qp_a) # if use cvxopt
    q_op =  np.array(sol['x'])
    # q_op = qp(qp_G, qp_a, None, None, 0) # if use quadprog
    
    # output
    x_dot = (v_r[0] + q_op[0]) * np.cos(t_r[0])
    y_dot = (v_r[0] + q_op[0]) * np.sin(t_r[0])
    theta_dot = dt_r[0] + q_op[1]
    #v = np.sqrt(x_dot**2 + y_dot**2)
    v = x_dot*cos(t) + y_dot*sin(t)
    #print(str(e_hat))
    #print('%10.4f'%x_r[0]+'%10.4f'%y_r[0]+'%10.4f'%t_r[0]+'%10.4f'%x_dot+'%10.4f'%y_dot+'%10.4f'%theta_dot)
    

    return v, theta_dot
