#!/usr/bin/env python3.7

# Copyright 2021, Gurobi Optimization, LLC

# This example formulates and solves the following simple bilinear model:
#  maximize    x
#  subject to  x + y + z <= 10
#              x * y <= 2         (bilinear inequality)
#              x * z + y * z = 1  (bilinear equality)
#              x, y, z non-negative (x integral in second version)

import gurobipy as gp
from gurobipy import GRB
import numpy as np
import xlwt
import xlrd
import random
import time
import csv



def crf(year):
    i = 0.08
    crf=((1+i)**year)*i/((1+i)**year-1);
    return crf


def model_linear_cost(m,x1,x2,y1,y2,y3,power,capex):
    z1 = m.addVar(vtype=GRB.BINARY, name=f"z1")
    z2 = m.addVar(vtype=GRB.BINARY, name=f"z2")
    w1 = m.addVar(vtype=GRB.CONTINUOUS, name=f"w1")
    w2 = m.addVar(vtype=GRB.CONTINUOUS, name=f"w2")
    w3 = m.addVar(vtype=GRB.CONTINUOUS, name=f"w3")
    m.addConstr(w1+w2+w3 == 1)
    m.addConstr(z1+z2==1)
    m.addConstr(w1<=z1)
    m.addConstr(w2<=z1+z2)
    m.addConstr(w3<=z2)
    m.addConstr(power == x1*w2+x2*w3)
    m.addConstr(capex == y1*w1+y2*w2+y3*w3)
    return m



def planning_problem(dict,isloate,input_json):
    t0 = time.time()
    #lambda_ele_in = [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.7, 1, 1, 1, 1,
    #                 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 1.2, 1.2, 1.2, 1.2, 1.2, 0.4]*365
    #0.9935,0.6713,0.53,0.3155,
    big_wind = [0.53,0.53,0.53,0.53,0.6713,0.6713,0.6713,0.6713,0.6713,0.6713,0.53,0.53,0.53,0.53,0.53,0.6713,0.6713,0.9935,0.9935,0.9935,0.9935,0.6713,0.6713,0.6713]
    small_wind = [0.6713,0.6713,0.6713,0.6713,0.6713,0.9935,0.9935,0.6713,0.6713,0.6713,0.3155,0.3155,0.3155,0.3155,0.3155,0.6713,0.6713,0.9935,0.9935,0.9935,0.9935,0.6713,0.6713,0.6713]

    # lambda_ele_in = [0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.7, 0.8, 0.8, 0.8, 0.8,
    #                  0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.8, 0.8, 0.8, 0.8, 0.8, 0.6]*365
    lambda_ele_in = big_wind*(31*3+30+28)+small_wind*(31*2+30)+big_wind*(31*2+30*2)


    lambda_ele_in = input_json['price']['TOU_power']*365


    lambda_ele_out = input_json['price']['power_sale']
    lambda_h = input_json['price']['hydrogen_price']
    cer=1
    #lambda_carbon = 0.06
    #p_transformer = 10000
    #lambda_fc = 15000
    tau = 1
    c = 4.2/3600
    M = 1000000
    epsilon = 0.0000001
    #cost_heat = 6.3*14356/4
    s_sum = input_json['renewable_energy']['pv_sc_max']

    crf_fc =    crf(input_json['device']['fc']['crf'])
    crf_el =    crf(input_json['device']['el']['crf'])
    crf_hst =   crf(input_json['device']['hst']['crf'])
    crf_water = crf(input_json['device']['ht']['crf'])
    crf_pv =    crf(input_json['device']['pv']['crf'])
    crf_sc =    crf(input_json['device']['sc']['crf'])
    #crf_pump =  crf(input_jso['device']n['']['crf'])
    crf_eb =    crf(input_json['device']['eb']['crf'])
    crf_hp =    crf(input_json['device']['hp']['crf'])
    crf_hpg =   crf(input_json['device']['ghp']['crf'])
    crf_gtw =   crf(input_json['device']['gtw']['crf'])
    crf_co =    crf(input_json['device']['co']['crf'])

    cost_hp = input_json['device']['hp']['cost']
    cost_hpg = input_json['device']['ghp']['cost']
    cost_eb = input_json['device']['eb']['cost']
    #cost_ec = 3326.613
    cost_fc = input_json['device']['fc']['cost']
    cost_el = input_json['device']['el']['cost']
    cost_hst = input_json['device']['hst']['cost']
    cost_ht = input_json['device']['ht']['cost'] # rmb/kg 180 # yuan/kwh
    cost_co = input_json['device']['co']['cost']
    cost_pv = input_json['device']['pv']['cost']
    #cost_pump = 730
    cost_gtw = input_json['device']['gtw']['cost']
    cost_sc = input_json['device']['sc']['cost']
    #s_solar = 1200
    #s_pv = 1500
    #t_water = 15
    #q_ac_nominal = 800
    #area_pv = 1500

    #mu_fc_e = 1.421
    #mu_fc_g = 1.989
    eta_ex = 0.95
    #eta_solar_loss = 0.035/1000000
    #eta_solar = 0.8
    eta_loss = 0.02/1000000
    eta_pv = input_json['device']['pv']['beta_pv']

    # m_fc_ex = 600000
    # m_solar = 100
    # m_solar_ex = 100
    # m_dht = 1400
    #m_ht = 1800000
    #m_ct = 1800000

    #hst = 10000 #储氢量
    #p_el_max = 25*46 #功率
    #p_fc_max = 500 #功率

    #alpha_ele = 1.01
    #alpha_heat = 0.351
    #alpha_hydrogen = 0

    #k_el = 0.022
    k_co = input_json['device']['co']['beta_co']
    k_fc_p = input_json['device']['fc']['eta_fc_p']
    k_fc_g = input_json['device']['fc']['eta_ex_g']
    k_el = input_json['device']['el']['beta_el']

    k_hp_g = input_json['device']['hp']['beta_hpg']
    k_hp_q = input_json['device']['hp']['beta_hpq']
    k_hpg_g = input_json['device']['ghp']['beta_ghpg']
    k_hpg_q = input_json['device']['ghp']['beta_ghpq']
    k_eb = input_json['device']['eb']['beta_eb']
    k_sc = input_json['device']['sc']['beta_sc']
    theta_ex = input_json['device']['sc']['theta_ex']
    p_gtw = input_json['device']['gtw']['beta_gtw']

    ele_load = dict['ele_load']
    g_demand = dict['g_demand']
    q_demand = dict['q_demand']
    r_solar = dict['r_solar']

    #--------------

    # import matplotlib.pyplot as plt
    # x = [i for i in range(0,24*6)]
    # plt.plot(x,g_de)
    # plt.show()
    # exit(0)


    period = len(q_demand)
    print(period)
    # Create a new model
    m = gp.Model("mip1")

    z_fc = [m.addVar(lb=0, ub=1, vtype=GRB.BINARY, name=f"z_fc{t}") for t in range(period)]

    z_el = [m.addVar(lb=0, ub=1, vtype=GRB.BINARY, name=f"z_el{t}") for t in range(period)]

    #z_ele_in = [m.addVar(lb=-0.0001, ub=1.01, vtype=GRB.BINARY, name=f"z_ele_in{t}") for t in range(period)]

    #z_ele_out = [m.addVar(lb=-0.0001, ub=1.01, vtype=GRB.BINARY, name=f"z_ele_out{t}") for t in range(period)]
    
    s_pv = m.addVar(vtype=GRB.CONTINUOUS, lb=0,  name=f"s_pv")#ub=13340,
    s_sc = m.addVar(vtype=GRB.CONTINUOUS, lb=0,  name=f"s_sc")

    capex_fc = m.addVar(vtype=GRB.CONTINUOUS, lb=0,  name=f"capex_fc")
    capex_el = m.addVar(vtype=GRB.CONTINUOUS, lb=0,  name=f"capex_el")

    num_gtw = m.addVar(vtype=GRB.INTEGER,lb=0,name='num_gtw')
    # Create variables

    #ce_h = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="ce_h")

    #m_ht = m.addVar(vtype=GRB.CONTINUOUS, lb=10, name="m_ht") # capacity of hot water tank

    g_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_hp{t}") for t in range(period)]# 热泵产热
    g_hpg = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_hpg{t}") for t in range(period)]# 热泵产热
    g_hpg_gr = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_hpg_gr{t}") for t in range(period)]# 热泵灌热
    q_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"q_hp{t}") for t in range(period)]# 热泵产热
    q_hpg = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"q_hpg{t}") for t in range(period)]# 热泵产热


    p_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0,name=f"p_hp{t}") for t in range(period)]#热泵产热耗电 ub = 268,
    p_hp_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0,ub = input_json["device"]["hp"]["power_max"], name=f"p_hp_max")

    p_hpc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_hpc{t}") for t in range(period)]#热泵产冷的耗电,ub = 202
    p_hpc_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0,ub = input_json["device"]["hp"]["power_max"],  name=f"p_hpc_max")

    p_hpg = [m.addVar(vtype=GRB.CONTINUOUS, lb=0,name=f"p_hpg{t}") for t in range(period)]#热泵产热耗电 ub = 268,
    p_hpg_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0,ub = input_json["device"]["ghp"]["power_max"], name=f"p_hpg_max")

    p_hpgc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_hpgc{t}") for t in range(period)]#热泵产冷的耗电,ub = 202
    p_hpgc_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0,ub = input_json["device"]["ghp"]["power_max"],  name=f"p_hpgc_max")


    m_hp = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_hp{t}") for t in range(period)]#热泵供热换水量
    # m_hpc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_hpc{t}") for t in range(period)]#热泵供冷换水量

    m_eb = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_eb{t}") for t in range(period)]#电锅炉换水量

    p_eb = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_eb{t}") for t in range(period)]#电锅炉耗电

    p_eb_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0,ub = input_json["device"]["eb"]["power_max"], name=f"p_eb_max")

    g_eb = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb{t}") for t in range(period)]#电锅炉产热

    p_co = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_co{t}") for t in range(period)]
    p_co_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0,ub = input_json["device"]["co"]["power_max"], name=f"p_co_max")
    p_pv = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pv{t}") for t in range(period)]

    t_ht = [m.addVar(vtype=GRB.CONTINUOUS, lb=55, ub = 90 ,name=f"t_ht{t}") for t in range(period)] # temperature of hot water tank

    m_ht = m.addVar(vtype=GRB.CONTINUOUS, lb=0,ub = 1800000, name=f"m_ht")

    m_ct = m.addVar(vtype=GRB.CONTINUOUS, lb=0,ub = 1800000, name=f"m_ct")

    t_ct = [m.addVar(vtype=GRB.CONTINUOUS, lb=2 , ub = 9, name=f"t_ct{t}") for t in range(period)] # temperature of cold water tank

    #m_ct = 

    # q_ec = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"q_ec{t}") for t in range(period)]# electric-cold unit 产冷
    # p_ec = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_ec{t}") for t in range(period)] # 耗电
    # p_ec_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_ec_max")


    g_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc{t}") for t in range(period)] # heat generated by fuel cells
    p_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_fc{t}") for t in range(period)] # 燃料电池产电
    p_fc_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_fc_max")
    #fc_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="fc_max") # rated heat power of fuel cells
    g_sc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_sc{t}") for t in range(period)]
    #pump_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="pump_max")

    p_el_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="p_el_max") # rated heat power of fuel cells

    #t_de = [m.addVar(vtype=GRB.CONTINUOUS, lb=0,name=f"t_de{t}") for t in range(period)] # outlet temparature of heat supply circuits

    h_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_fc{t}") for t in range(period)] # hydrogen used in fuel cells


    #m_fc = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_fc") # fuel cells water

    #m_el = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_el") # fuel cells water

    #g_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_el{t}") for t in range(period)] # heat generated by Electrolyzer

    h_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_el{t}") for t in range(period)] # hydrogen generated by electrolyzer

    p_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_el{t}") for t in range(period)] # power consumption by electrolyzer

    #t_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_el{t}") for t in range(period)] # outlet temperature of electrolyzer cooling circuits

    h_sto = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_sto{t}") for t in range(period)] # hydrogen storage 非季节储氢

    h_ssto = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_sto{t}") for t in range(365)] # 季节性储氢

    h_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_pur{t}") for t in range(period)] # hydrogen purchase

    p_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pur{t}") for t in range(period)] # power purchase

    p_sol = [m.addVar(vtype=GRB.CONTINUOUS, lb=0,name=f"p_sol{t}") for t in range(period)] # power purchase

    cost_c_ele = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"cost_c_ele")

    cost_c_heat = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"cost_c_heat")

    cost_c_cool = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"cost_c_cool")

    cost_c_m = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"cost_c_m")

    cost_c = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"cost_c")
    #p_pump = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump{t}") for t in range(period)] 

    hst = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"hst")

    #p_co = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_co{t}") for t in range(period)] 
    #m.addConstr(m_el+m_fc <= 0.001*m_ht)

    # 每日水罐温度平衡，非季节储氢量平衡
    #for i in range(int(period/24)-1):
        #m.addConstr(t_ht[i*24+24] == t_ht[24*i])
        #m.addConstr(t_ct[i*24+24] == t_ct[24*i])
        #m.addConstr(h_sto[i*24+24] == h_sto[24*i])
    m.addConstr(t_ht[-1] == t_ht[0])
    m.addConstr(t_ct[-1] == t_ct[0])
    m.addConstr(h_sto[-24] == h_sto[0])


    m.addConstr(num_gtw<=input_json['device']['gtw']['number_max'])
    m.addConstr(p_fc_max<=input_json['device']['fc']['power_max'])
    m.addConstr(p_fc_max>=input_json['device']['fc']['power_min'])
    m.addConstr(p_hpg_max<=input_json['device']['ghp']['power_max'])
    m.addConstr(p_hpg_max>=input_json['device']['ghp']['power_min'])
    m.addConstr(p_hp_max<=input_json['device']['hp']['power_max'])
    m.addConstr(p_hp_max>=input_json['device']['hp']['power_min'])
    m.addConstr(p_eb_max<=input_json['device']['eb']['power_max'])
    m.addConstr(p_eb_max>=input_json['device']['eb']['power_min'])
    m.addConstr(p_el_max<=input_json['device']['el']['power_max'])
    m.addConstr(p_el_max>=input_json['device']['el']['power_min'])
    m.addConstr(hst<=input_json['device']['hst']['sto_max'])
    m.addConstr(hst>=input_json['device']['hst']['sto_min'])
    m.addConstr(m_ht<=input_json['device']['ht']['water_max'])
    m.addConstr(m_ht>=input_json['device']['ht']['water_min']) 
    m.addConstr(m_ct<=input_json['device']['ct']['water_max'])
    m.addConstr(m_ct>=input_json['device']['ct']['water_min']) 
    m.addConstr(s_pv<=input_json['device']['pv']['area_max'])
    m.addConstr(s_pv>=input_json['device']['pv']['area_min']) 
    m.addConstr(s_sc<=input_json['device']['sc']['area_max'])
    m.addConstr(s_sc>=input_json['device']['sc']['area_min']) 
    m.addConstr(p_co_max<=input_json['device']['co']['power_max'])
    m.addConstr(p_co_max>=input_json['device']['co']['power_min'])


    # m.addConstr(p_el_max == 56818)
    # #m.addConstr(hst == )
    # m.addConstr(p_fc_max == 5293)
    # m.addConstr(p_ec_max == 195)
    # m.addConstr(p_hp_max == 0)
    #m.addConstr(s_pv == 70190)
    # 储能约束
    for i in range(period - 1):
        # hot water tank and heat supply
        m.addConstr(c*m_ht*(t_ht[i + 1] - t_ht[i]) + g_demand[i] +g_hpg_gr[i] == 
            g_fc[i] + g_hp[i] + g_eb[i] + g_hpg[i])

        # cold water tank and cold supply
        m.addConstr(c*m_ct * (t_ct[i] - t_ct[i+1]) + q_demand[i] == q_hp[i] +q_hpg[i])
        #if i%24 == 0 and int(i/24)<364:
            #m.addConstr(m_ct * (t_ct[i] - t_ct[i+1]) + q_demand[i]/c == m_hpc[i] * (5) +m_ec[i]*(5)  - eta_loss*m_ct*(t_ct[i] - 16))
            #m.addConstr(h_sto[i+1] - h_sto[i] + h_ssto[int(i/24)+1] - h_ssto[int(i/24)] == h_pur[i] + h_el[i] - h_fc[i])

        #else:
            #m.addConstr(m_ct * (t_ct[i] - t_ct[i+1]) + q_demand[i]/c == m_hpc[i] * (5) +m_ec[i]*(5)  - eta_loss*m_ct*(t_ct[i] - 16))
        m.addConstr(h_sto[i+1] - h_sto[i] == h_pur[i] + h_el[i] - h_fc[i])
        
    m.addConstr(c*m_ht * (t_ht[0] - t_ht[-1]) + g_demand[-1] +g_hpg_gr[-1] == g_fc[-1]+g_hp[-1]+g_eb[-1]+ g_hpg[-1])
    m.addConstr(c*m_ct * (t_ct[-1] - t_ct[0]) + q_demand[-1] ==  q_hp[-1] +q_hpg[-1])
    m.addConstr(h_sto[0] - h_sto[-1] == h_pur[-1] + h_el[-1] - h_fc[-1])
    #m.addConstr(h_sto[0] - h_sto[-1] + h_ssto[0] - h_ssto[-1] == h_pur[-1] + h_el[-1] - h_fc[-1])
    #m.addConstr(t_ht[0] == 60)
    #m.addConstr(h_ssto[-1] == h_ssto[0])
    m.addConstr(gp.quicksum(q_hpg)-gp.quicksum(p_hpgc)+gp.quicksum(g_hpg_gr) == gp.quicksum(g_hpg)-gp.quicksum(p_hpg))
    #piecewise price
    m = model_linear_cost(m,300,600,10,310,439,p_el_max,capex_el)
    m = model_linear_cost(m,300,600,10,310,490,p_fc_max,capex_fc)
    #m.addConstr(s_pv*cost_pv +s_sc*cost_sc +p_hpg_max*cost_hpg +cost_gtw*num_gtw +cost_ht*m_ht+cost_ht*m_ct+cost_hst*hst+cost_eb*p_eb_max+cost_hp*p_hp_max+cost_fc*p_fc_max+cost_el*p_el_max + 10*gp.quicksum([p_pur[i]*lambda_ele_in[i] for i in range(period)])-10*gp.quicksum(p_sol)*lambda_ele_out+10*lambda_h*gp.quicksum(h_pur)+954>=0 ) 
    m.addConstr(s_pv*cost_pv +s_sc*cost_sc +p_hpg_max*cost_hpg +cost_gtw*num_gtw +cost_ht*m_ht+cost_ht*m_ct+cost_hst*hst+cost_eb*p_eb_max+cost_hp*p_hp_max+cost_fc*p_fc_max+cost_el*p_el_max <= input_json['price']['capex_max'])
    for i in range(period):
        #电网
        m.addConstr(p_pur[i] <= 1000000000*(isloate[0]))
        m.addConstr(p_sol[i] <= 1000000000*(isloate[1]))
        m.addConstr(h_pur[i] <= 1000000000*(isloate[2]))
        # 燃料电池
        m.addConstr(g_fc[i] <= eta_ex*k_fc_g*h_fc[i])#氢燃烧产电
        m.addConstr(10000*z_fc[i]>=g_fc[i])
        #m.addConstr(g_fc[i] == c*m_fc[i]*(10))
        #m.addConstr(m_fc[i] <= g_fc[i]*100000)
        m.addConstr(p_fc[i] == k_fc_p*h_fc[i])

        m.addConstr(p_fc[i] <= p_fc_max)
        #m.addConstr(z_fc[i]+g_fc[i]>=0.01)

        # 电解槽
        m.addConstr(p_el[i] <= p_el_max)
        m.addConstr(h_el[i] <= k_el * p_el[i])
        m.addConstr(h_el[i] <= hst)

        # heat pump
        m.addConstr(p_hp[i]*k_hp_g == g_hp[i])
        m.addConstr(p_hp[i] <= p_hp_max)

        m.addConstr(p_hpc[i]*k_hp_q == q_hp[i])
        m.addConstr(p_hpc[i] <= p_hp_max)

        # hpg
        m.addConstr(p_hpg[i]*k_hpg_g == g_hpg[i])
        m.addConstr(p_hpg[i] <= p_hpg_max)

        m.addConstr(p_hpgc[i]*k_hpg_q == q_hpg[i])
        m.addConstr(p_hpgc[i] <= p_hpg_max)

        # compressor
        m.addConstr(p_co[i] == k_co * h_el[i])
        m.addConstr(p_co[i]<=p_co_max)

        # electric boilor 
        m.addConstr(k_eb*p_eb[i] == g_eb[i])
        m.addConstr(p_eb[i] <= p_eb_max)



        # hydrogen sto
        m.addConstr(h_sto[i]<=hst)

        # balance
        m.addConstr(p_el[i] + p_sol[i] + p_hp[i] +p_hpc[i] + p_hpg[i] + p_hpgc[i] + p_eb[i] + p_co[i]+ ele_load[i] == p_pur[i] + p_fc[i] + p_pv[i])

        # pv
        m.addConstr(p_pv[i] == eta_pv*s_pv*r_solar[i])
        # sc
        m.addConstr(g_sc[i] == k_sc*theta_ex*s_sc*r_solar[i])

        #psol
        m.addConstr(p_sol[i] <= p_fc[i]+p_pv[i])

    # area
    m.addConstr(s_pv+s_sc<=s_sum)
    m.addConstr(num_gtw*p_gtw>=p_hpg_max)


    # m.setObjective( crf_pv * cost_pv*area_pv+ crf_el*cost_el*el_max
    #     +crf_hst * hst*cost_hst +crf_water* cost_water_hot*m_ht + crf_fc *cost_fc * fc_max + lambda_h*gp.quicksum(h_pur)*365+ 
    #     365*gp.quicksum([p_pur[i]*lambda_ele_in[i] for i in range(24)])-365*gp.quicksum(p_sol)*lambda_ele_out , GRB.MINIMIZE)
    m.addConstr(gp.quicksum(p_pur)<=cer*(sum(ele_load)+sum(g_demand)+sum(q_demand)))
    m.addConstr(cost_c_ele == sum([ele_load[i]*lambda_ele_in[i] for i in range(period)]))
    m.addConstr(cost_c_heat == sum([g_demand[i]/0.95*lambda_ele_in[i] for i in range(period)]))#/(3.41))
    m.addConstr(cost_c_cool == sum([q_demand[i]/4*lambda_ele_in[i] for i in range(period)]))#/3.8)
    m.addConstr(cost_c == cost_c_cool+cost_c_heat+cost_c_ele)
    m.setObjective(crf_pv*s_pv*cost_pv +crf_sc*s_sc*cost_sc + crf_hst*hst*cost_hst + crf_water*cost_ht*(m_ht+m_ct) + crf_hp*cost_hp*p_hp_max  + crf_hpg*cost_hpg*p_hpg_max + crf_gtw*cost_gtw*num_gtw
        + crf_eb*cost_eb*p_eb_max  +crf_fc*capex_fc+crf_el*capex_el+crf_co*p_co_max*cost_co
        + lambda_h*gp.quicksum(h_pur) + gp.quicksum([p_pur[i]*lambda_ele_in[i] for i in range(period)])-gp.quicksum(p_sol)*lambda_ele_out,GRB.MINIMIZE)
    #-gp.quicksum(p_sol)*lambda_ele_out
    # First optimize() call will fail - need to set NonConvex to 2
    m.params.NonConvex = 2
    m.params.MIPGap = 0.01
    # m.optimize()
    #print(m.status)

    try:
        m.optimize()
    except gp.GurobiError:
        print("Optimize failed due to non-convexity")
    #print([p_eb[i].X for i in range(period)])
    if m.status == GRB.INFEASIBLE:
        print('Model is infeasible')
        m.computeIIS()
        m.write('model.ilp')
        print("Irreducible inconsistent subsystem is written to file 'model.ilp'")

    op_c = sum([(ele_load[i]+g_demand[i]/k_eb+q_demand[i]/k_hpg_q)*lambda_ele_in[i] for i in range(period)])
    cap_sum = s_pv.X*cost_pv +s_sc.X*cost_sc +p_hpg_max.X*cost_hpg +cost_gtw*num_gtw.X +cost_ht*m_ht.X+cost_ht*m_ct.X+cost_hst*hst.X+cost_eb*p_eb_max.X+cost_hp*p_hp_max.X+capex_fc.X+capex_el.X+p_co_max.X*cost_co
    op_sum = sum([p_pur[i].X*lambda_ele_in[i] for i in range(period)])-sum([p_sol[i].X for i in range(period)])*lambda_ele_out+lambda_h*sum([h_pur[i].X for i in range(period)])
    revenue = input_json['load']['load_area']*(input_json['price']['heat_price']*len(input_json['load']['heat_mounth'])+input_json['price']['cold_price']*len(input_json['load']['cold_mounth']))
    #s_heat_sto = [q_hp[i].X - g_hp[i].X for i in range(period)]
    # for i in range(period-1):
    #     s_heat_sto[i+1]+=s_heat_sto[i]

    # output_json = {
    #     'ele_load':ele_load,#电负荷分时数据
    #     'g_demand': g_demand,#热负荷分时数据
    #     'q_demand': q_demand,#冷负荷分时数据
    #     'r_solar': r_solar,#光照强度分时数据

    #     'num_gtw':num_gtw.X,#地热井数目/个
    #     'p_fc_max':p_fc_max.X,#燃料电池容量
    #     'p_hpg_max':p_hpg_max.X,#地源热泵功率
    #     'p_hp_max':p_hp_max.X,#空气源热泵功率
    #     'p_eb_max':p_eb_max.X,#电热锅炉功率
    #     'p_el_max':p_el_max.X,#电解槽功率
    #     'hst':hst.X,#储氢罐容量/kg
    #     'm_ht':m_ht.X,#储热罐/kg
    #     'm_ct':m_ct.X,#冷水罐/kg
    #     'area_pv':s_pv.X,#光伏面积/m2
    #     'area_sc':s_sc.X,#集热器面积/m2

    #     "grid_receive_year":0,#并网投资回报年限
    #     "isloate_receive_year":0,#离网投资回报年限
    #     "grid_cer":0.5,#并网碳减排率
    #     "isloate_cer":0.5#离网碳减排率

    # }

    #规划输出
    output_json = {
            'ele_load_sum': format(sum(ele_load),'.2f'),  # 电负荷总量/kwh
            'g_demand_sum': format(sum(g_demand),'.2f'),  # 热负荷总量/kwh
            'q_demand_sum': format(sum(q_demand),'.2f'),  # 冷负荷总量/kwh
            'ele_load_max': format(max(ele_load),'.2f'),  # 电负荷峰值/kwh
            'g_demand_max': format(max(g_demand),'.2f'),  # 热负荷峰值/kwh
            'q_demand_max': format(max(q_demand),'.2f'),  # 冷负荷峰值/kwh
            'ele_load': ele_load,  # 电负荷8760h的分时数据/kwh
            'g_demand': g_demand,  # 热负荷8760h的分时数据/kwh
            'q_demand': q_demand,  # 冷负荷8760h的分时数据/kwh
            'r_solar': r_solar,  # 光照强度8760h的分时数据/kwh

            'num_gtw': num_gtw.X,  # 地热井数目/个
            'p_fc_max': format(p_fc_max.X,'.2f'),  # 燃料电池容量/kw
            'p_hpg_max': format(p_hpg_max.X,'.2f'),  # 地源热泵功率/kw
            'p_hp_max': format(p_hp_max.X,'.2f'),  # 空气源热泵功率/kw
            'p_eb_max': format(p_eb_max.X,'.2f'),  # 电热锅炉功率/kw
            'p_el_max': format(p_el_max.X,'.2f'),  # 电解槽功率/kw
            'hst': format(hst.X,'.2f'),  # 储氢罐容量/kg
            'm_ht': format(m_ht.X,'.2f'),  # 储热罐/kg
            'm_ct': format(m_ct.X,'.2f'),  # 冷水罐/kg
            'area_pv': format(s_pv.X,'.2f'),  # 光伏面积/m2
            'area_sc': format(s_sc.X,'.2f'),  # 集热器面积/m2
            'p_co': format(p_co_max.X,'.2f'),  #氢压机功率/kw

            "equipment_cost": format(cap_sum,'.2f'),  #设备总投资/万元
            "receive_year": format(cap_sum/(revenue-op_sum),'.2f'),  # 投资回报年限/年
    }
    device_cap = {
            'num_gtw': num_gtw.X,  # 地热井数目/个
            'p_fc_max': p_fc_max.X,  # 燃料电池容量/kw
            'p_hpg_max': p_hpg_max.X,  # 地源热泵功率/kw
            'p_hp_max': p_hp_max.X,  # 空气源热泵功率/kw
            'p_eb_max': p_eb_max.X,  # 电热锅炉功率/kw
            'p_el_max': p_el_max.X,  # 电解槽功率/kw
            'hst': hst.X,  # 储氢罐容量/kg
            'm_ht': m_ht.X,  # 储热罐/kg
            'm_ct': m_ct.X,  # 冷水罐/kg
            'area_pv': s_pv.X,  # 光伏面积/m2
            'area_sc': s_sc.X,  # 集热器面积/m2
            'p_co': p_co_max.X,  #氢压机功率/kw
    }
    #运行后的输出
    operation_output_json = {
            "operation_cost": op_sum,  # 年化运行成本/万元
            "cost_save_rate": (op_c-op_sum)/op_c,  #运行成本节约比例
            "co2":0,  #总碳排/t
            "cer":0,  #碳减排率
            "cer_perm2":200  #每平米的碳减排量/t
    }
    return {'objective':m.objVal,
            'process time':time.time() - t0,
            'cost_c_ele':cost_c_ele.X,
            'cost_c_heat':cost_c_heat.X,
            'cost_c_cool':cost_c_cool.X,
            'cost_c_m':cost_c_m.X,
            'cost_c':cost_c.X,
            'cap_fc':capex_fc.X,
            'cap_hp':cost_hp*p_hp_max.X,
            #'cap_hpc':cost_hpc*p_hpc_max.X,
            'cap_eb':cost_eb*p_eb_max.X,
            #'cap_ec':cost_ec*p_ec_max.X,
            'cap_hst':cost_hst*hst.X,
            'cap_ht':cost_ht*m_ht.X,
            #'cap_ct':cost_ht*m_ct,
            'cap_pv':s_pv.X*cost_pv,
            'cap_el':capex_el.X,
            #s_pv.X*cost_pv
            'num_gtw':num_gtw.X,
            'p_fc_max':p_fc_max.X,
            'p_hpg_max':p_hpg_max.X,
            'p_hp_max':p_hp_max.X,
            'p_eb_max':p_eb_max.X,
            #'p_ec_max':p_ec_max.X,
            'p_el_max':p_el_max.X,
            'hst':hst.X,
            'm_ht':m_ht.X,
            'm_ct':m_ct.X,
            'area_pv':s_pv.X,
            'area_sc':s_sc.X,
            #'cer': cer.x,
            #'ce_h': pulp.value(ce_h),
            #'ce_c': pulp.value(ce_c),
            #'cost_c_heat':pulp.value(cost_c_heat),
            #'cost_c_cooling':pulp.value(cost_c_cooling),
            'h_cost' : lambda_h*sum([h_pur[i].X for i in range(period)]),
            'p_cost' : sum([p_pur[i].X*lambda_ele_in[i] for i in range(period)]),
            'p_sol_earn':-sum([p_sol[i].X for i in range(period)])*lambda_ele_out,
            'opex':sum([p_pur[i].X*lambda_ele_in[i] for i in range(period)])-sum([p_sol[i].X for i in range(period)])*lambda_ele_out+lambda_h*sum([h_pur[i].X for i in range(period)]),
            'cap_sum': s_pv.X*cost_pv +s_sc.X*cost_sc +p_hpg_max.X*cost_hpg +cost_gtw*num_gtw.X +cost_ht*m_ht.X+cost_ht*m_ct.X+cost_hst*hst.X+cost_eb*p_eb_max.X+cost_hp*p_hp_max.X+capex_fc.X+capex_el.X,

            'cer':sum([p_pur[i].X for i in range(period)])/(sum(ele_load)+sum(g_demand)+sum(q_demand)),
            'cer_self':sum([p_sol[i].X for i in range(period)])/(sum(ele_load)+sum(g_demand)+sum(q_demand)),
            'ele_load':dict['ele_load'],
            'g_demand':dict['g_demand'],
            'q_demand':dict['q_demand'],
            #'m_demand':dict['m_demand'],
            'p_pur' : [p_pur[i].X for i in range(period)],
            'p_sol' : [p_sol[i].X for i in range(period)],
            'h_pur' : [h_pur[i].X for i in range(period)],
            #'g_solar': [eta_solar*s_solar*r_solar[i] for i in range(period)],
            'p_pv': [eta_pv*s_pv.X*r_solar[i] for i in range(period)],
            #'z_fcex':[pulp.value(z_fcex[i]) for i in range(period)],
            #'z_exon':[pulp.value(z_exon[i]) for i in range(period)],
            #'z_s':[pulp.value(z_s[i]) for i in range(period)],
            #'v_fc':[pulp.value(v_fc[i]) for i in range(period)],
            'p_fc':[p_fc[i].X for i in range(period)],
            'g_fc':[g_fc[i].X for i in range(period)],
            'h_fc':[h_fc[i].X for i in range(period)],
            'p_el':[p_el[i].X for i in range(period)],
            'h_el':[h_el[i].X for i in range(period)],
            'p_hp':[p_hp[i].X for i in range(period)],
            'g_hp':[g_hp[i].X for i in range(period)],
            'p_hpc':[p_hpc[i].X for i in range(period)],
            'q_hp':[q_hp[i].X for i in range(period)],
            'p_hpg':[p_hpg[i].X for i in range(period)],
            'p_hpgc':[p_hpgc[i].X for i in range(period)],
            'q_hpg':[q_hpg[i].X for i in range(period)],
            'g_hpg':[g_hpg[i].X for i in range(period)],
            #'t_fc_ex':[pulp.value(t_fc_ex[i]) for i in range(period)],
            't_ht':[t_ht[i].X for i in range(period)],
            'h_sto':[h_sto[i].X for i in range(period)],
            #'t_solar':[pulp.value(t_solar[i]) for i in range(period)],
            #'g_solar_ex':[pulp.value(g_solar_ex[i]) for i in range(period)],
            #'t_solar_exout':[pulp.value(t_solar_exout[i]) for i in range(period)],
            #'w_solar_ex':[pulp.value(w_solar_ex[i]) for i in range(period)],
            'p_eb':[p_eb[i].X for i in range(period)],
            'g_eb':[g_eb[i].X for i in range(period)],
            #'m_eb':[m_eb[i].X for i in range(period)],
            'g_hpg_gr':[g_hpg_gr[i].X for i in range(period)],
            #'m_fc':[m_fc[i].X for i in range(period)],
            #'m_ec':[m_ec[i].X for i in range(period)],
            #'m_hp':[m_hp[i].X for i in range(period)],
            #'h_ssto':[h_ssto[i].X for i in range(365)],
            #'h_loss' : [eta_loss*m_ht*(t_ht[i].X - t_env_indoor[i]) for i in range(period)],
            #'t_eb':[t_eb[i].X for i in range(period)],
            #'t_return':[pulp.value(t_return[i]) for i in range(period)],
            #'t_ac':[pulp.value(t_ac[i]) for i in range(period)],
            #'t_cr':[pulp.value(t_cr[i]) for i in range(period)],
            't_ct':[t_ct[i].X for i in range(period)]
            #'q_ac':[pulp.value(c*m_ac*(t_cr[i] - t_ac[i])) for i in range(period)],
            #'g_fc':[eta_ex*mu_fc_g*h_fc[i].X for i in range(period)],
            #'g_htv':[pulp.value(c*m_ht*(t_ht[i+1] - t_ht[i])) for i in range(period)],
            #'g_eb':[eta_eb*p_eb[i].X for i in range(period)]
            #'g_shtv':[pulp.value(g_sht[i+1] - g_sht[i]) for i in range(period)]
            },output_json,operation_output_json,device_cap




# if __name__ == '__main__':
#     period = 8760

#     #book_spr = xlrd.open_workbook('cspringdata.xlsx')
#     #book_sum = xlrd.open_workbook('csummerdata.xlsx')
#     #book_aut = xlrd.open_workbook('cautumndata.xlsx')
#     #book_win = xlrd.open_workbook('cwinterdata.xlsx')

    

#     #print(len(r_solar),len(t_env_indoor),len(t_env_outdoor))
#     #print(max(r_solar))
#     #exit(0)
#     # book = xlrd.open_workbook('new_xls.xlsx')
#     # data = book.sheet_by_index(0)
#     # for l in range(1,8761):
#     #     q_demand.append(data.cell(l,1).value)
#     #     g_demand.append(data.cell(l,2).value)
#     #     m_demand.append(data.cell(l,3).value)
#     #     ele_load.append(data.cell(l,4).value)
#     # q_demand = [0 if num == '' else num for num in q_demand]
#     # g_demand = [0 if num == '' else num for num in g_demand]
#     # m_demand = [0 if num == '' else num for num in m_demand]
#     # ele_load = [0 if num == '' else num for num in ele_load]
#     #print(q_demand)
#     #exit(0)
#     # for l in range(1,8761):
#     #     q_demand.append(float(data.cell(l,1).value))
#     #     g_demand.append(float(data.cell(l,2).value))
#     #     m_demand.append(float(data.cell(l,3).value)/(30*c))
#     #     ele_load.append(float(data.cell(l,4).value))
#     ele_load = [0 for i in range(8760)]
#     g_demand = [0 for i in range(8760)]
#     q_demand = [0 for i in range(8760)]
#     r_solar =  [0 for i in range(8760+24)]
#     with open('load.csv') as officecsv:

#         office = csv.DictReader(officecsv)
#         i=0
#         for row in office:
#             ele_load[i] += float(row['Electricity Load [J]'])
#             q_demand[i] += float(row['Cooling Load [J]'])
#             g_demand[i] += float(row['Heating Load [J]'])
            
#             i+=1
#     print(sum(g_demand),sum(q_demand),sum(ele_load))
#     #book = xlrd.open_workbook('renewable.csv')
#     with open('renewable1.csv') as renewcsv:
#         renewcsv.readline()
#         renewcsv.readline()
#         renewcsv.readline()
#         renew = csv.DictReader(renewcsv)
        
#         i=0
#         for row in renew:

#             r_solar[i] += float(row['radiation_surface'])
#             i+=1
#     #print(r_solar)
#     q_demand[:92*24] = [0 for i in range(92*24)]
#     q_demand[-61*24:] = [0 for i in range(61*24)]
#     g_demand[92*24:92*24+212*24] = [0 for i in range(212*24)]
#     r_solar = r_solar[-8:]+r_solar[:-8]
#     r_solar = [r_solar[i]/1000 for i in range(period)]

#     kkk = 12000
#     tmp_sum = sum(ele_load)+sum(q_demand)/4+sum(g_demand)/0.95
#     kkk2 = 10000000/tmp_sum
#     g_demand = [g_demand[i]*kkk for i in range(period)]
#     q_demand = [q_demand[i]*kkk for i in range(period)]
#     ele_load = [ele_load[i]*kkk for i in range(period)]
#     #print(max(g_demand),max(q_demand),max(ele_load))
#     #print(sum(g_demand),sum(q_demand),sum(ele_load))
#     #exit(0)
#     #s_e = sum(ele_load)
#     #s_s = sum(r_solar)
#     #ele_load = [ele_load[i]*4971355/s_e for i in range(period)]
#     #g_demand = [g_demand[i] for i in range(period)]
#     #q_demand = [q_demand[i] for i in range(period)]
#     #r_solar = [r_solar[i]*1362/s_s for i in range(period)]
#     print(max(g_demand),max(q_demand),max(ele_load))
#     print(sum(g_demand),sum(q_demand),sum(ele_load))
#     # print(len(r_solar))
#     # exit(0)

#     dict = {'ele_load': ele_load, 'g_demand': g_demand, 'q_demand': q_demand, 'r_solar': r_solar}

#     res = operating_problem(dict, 8760)

#     items = list(res.keys())
#     wb = xlwt.Workbook()
#     total = wb.add_sheet('garden')
#     for i in range(len(items)):
#         total.write(0,i,items[i])
#         if type(res[items[i]]) == list:
#             sum = 0
#             print(items[i])
#             for j in range(len(res[items[i]])):
#                 total.write(j+2,i,(res[items[i]])[j])
#                 # sum += (res[items[i]])[j]
#             # total.write(1,i,sum)
#         else:
#             total.write(1,i,res[items[i]])

#     filename = 'res/chicken_plan_2_load_1' + '.xls'
#     wb.save(filename)

