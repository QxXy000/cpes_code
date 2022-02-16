# %load main.py
import sys
import numpy as np
import random
import pandas as pd
import time
import pickle
import xlrd
import xlwt
import csv
import gurobipy as gp
from gurobipy import GRB
from itertools import islice
import json

def verify_dimension(dict):
    for value in dict:
        if len(dict[value]) != period:
            print('[WARNING] The dimension of ' + value +' is not correct')
            sys.exit()

def season_operating_problem(dict_load,device_cap,isolate,tem_env,input_json,period):
    t0=time.time()
    # power price in winter, autumn and spring
    # lambda_ele_in = [0.3748,0.3748,0.3748,0.3748,0.3748,0.3748,0.3748,0.8745,0.8745,0.8745,1.4002,1.4002,1.4002,1.4002,
    #                  1.4002,0.8745,0.8745,0.8745,1.4002,1.4002,1.4002,0.8745,0.8745,0.3748]*7
    # power price in summer
    lambda_ele_in = [0.4096, 0.4096, 0.4096, 0.4096, 0.4096, 0.4096, 0.4096, 0.7704, 1.1313, 1.1313, 1.1313, 1.1313,
                     0.7704, 0.7704, 0.7704, 0.7704, 0.7704, 0.7704, 1.1313, 1.1313, 1.1313, 1.1313, 1.1313, 0.4096] * 7
    lambda_ele_in = input_json['price']['TOU_power']*7
    lambda_ele_out = input_json['price']['power_sale']
    lambda_h = input_json['price']['hydrogen_price']
    lambda_carbon = 0.06

    p_transformer = 100000

    alpha_e = 0.5839#电网排放因子kg/kWh
    alpha_gas = 1.535#天然气排放因子kg/Nm3
    #alpha_heat = 0.351
    alpha_H2=1.74#氢排放因子
    alpha_eo=0.8922#减排项目基准排放因子
    #k_co_b = 0.05
    #k_co_el = 1.02
    k_pv=0.21#光伏效率
    k_co=1.399#压缩机COP1.399kWh/kg
    k_el = 0.022
    k_stc=input_json['device']['sc']['beta_sc']#集热器效率
    k_eb=0.95#电锅炉效率COP
    miu_stc_loss=0.035#集热器损耗系数
    miu_loss=0.02#W(m2*K)热水罐损耗系数
    theta_ex=0.95#热交换器效率
    yita_fc_e_nominal=15#燃料电池产电COP15kWh/kg
    yita_fc_g_nominal=16.6#燃料电池产热COP16.6kWh/kg
    yita_hp_g=3#空气源热泵制热COP
    yita_hp_q=4#空气源热泵制冷COP
    yita_ghp_g=3.54#地源热泵制热COP
    yita_ghp_q=4#地源热泵制冷COP
    

    # g_loss = 200
    # q_loss = 100
    g_storage = 1000
    q_storage = 1000

    ele_load = dict_load['ele_load']
    g_demand = dict_load['g_demand']
    q_demand = dict_load['q_demand']
    r_solar = dict_load['r_solar']

    
    g_ac_nominal = 200#额定
    p_fc_nominal_lower=0#p_fc下界
    u_el_upper=3#输出压强上限3MPa
    u_el_lower=0.1#输出压强下限0.1MPa
    u_ht_upper=35#储氢罐压强上限35MPa
    u_ht_lower=0.5#储氢罐压强下限0.5MPa
    T_wt_upper=82#℃热水罐储水温度上限
    T_wt_lower=4#℃热水罐储水温度下限
    T_ct_upper=25#℃冷水罐储水温度上限
    T_ct_lower=3#℃冷水罐储水温度下限
    T_g_lower=55#℃供热温度下限
    T_q_lower=9#℃供冷温度上限
    
    c = 4.2/3600    #水的比热容，4.2KJ/(kg*K)，已转换成KWH
    ro_wt=1000  #水密度(kg/m3)
    epsilon=0.0000001
    M = 1000000000
    
    V_c=10  #m3燃料电池回路体积
    V_stc=50#太阳能集热器内部体积
    V_stc_ex=5#m3太阳能集热器回路
    
    
    t_fc=85#燃料电池冷却液流入换热器的温度
    
    
    A_stc=100#输入的参数，防冻液管与外界接触的表面积
    S_stc=device_cap["area_sc"]#输入的参数，太阳能集热板吸收太阳能的面积
    S_pv=device_cap["area_pv"] #输入的参数，光伏表面积
    m_wt=device_cap["m_ht"] #输入的参数，热水罐质量容量
    m_ct=device_cap["m_ct"] #输入的参数，冷水罐质量容量
    m_inout_upper = device_cap["hst"] #输入的参数，储氢罐质量容量
    p_el_nominal = device_cap["p_el_max"] #输入的参数，电解槽额定功率
    p_fc_nominal = device_cap["p_fc_max"] #输入的参数，燃料电池额定功率
    p_eb_nominal= device_cap["p_eb_max"] #输入的参数，电锅炉额定功率
    p_hp_nominal= device_cap["p_hp_max"]#输入的参数，空气源热泵额定功率
    p_ghp_nominal=device_cap["p_hpg_max"]#输入的参数，地源热泵额定功率
    p_co_nominal=device_cap["p_co"]#输入的参数，地源热泵额定功率
    
    coeff_el_h2u=u_el_upper/k_el/p_el_nominal if p_el_nominal!=0 else 100000 #输出氢气质量换算成压强的系数
    coeff_ht_h2u=u_ht_upper/m_inout_upper if m_inout_upper!=0 else 100000#储氢罐氢气换算成压强系数
    m_fc_w=ro_wt*V_c#燃料电池回路水的质量
    m_stc=ro_wt*V_stc#太阳能集热器水的质量
    m_stc_ex=ro_wt*V_stc_ex#太阳能集热器回路水的质量
    m_eb=p_eb_nominal/c/(85-60)#供热水回路流量，额定产热量除以(供回水路温差*比热容)
    m_hp_g=p_hp_nominal/c/(55-40)#空气源热泵供热水回路流量,额定产冷量除以(供回水路温差*比热容)，先用的地源热泵的温度差
    m_hp_q=p_hp_nominal/c/(12-7)#空气源热泵供冷水回路流量,额定产冷量除以(供回水路温差*比热容)
    m_ghp_g=p_ghp_nominal/c/(55-40)#地源热泵供热水回路流量,额定产冷量除以(供回水路温差*比热容)
    m_ghp_q=p_ghp_nominal/c/(12-7)#地源热泵供冷水回路流量,额定产冷量除以(供回水路温差*比热容)
    A_wt=pow(m_wt/ro_wt,2/3)*6#热水罐表面积
    A_ct=pow(m_ct/ro_wt,2/3)*6#热水罐表面积
    m_io=m_wt#热水罐的换水量，后续要改
    m_cio=m_ct#冷水罐的换水量，后续要改
    
    temperature =[26.32, 25.57, 24.6, 24.4, 23.85, 24.9, 25.68, 26.41, 27.2, 28.36, 30.97, 31.3, 33.65, 35.29, 35.5, 33.7, 32.45,
    31.8, 30.87, 29.79, 28.7, 27.7, 26.79, 25.97]   #夏季室外温度
    # temperature = np.array(
    #     [6.32, 5.57, 4.6, 4.4, 3.85, 4.9, 5.68, 6.41, 7.2, 8.36, 0.97, 11.3, 13.65, 15.29, 15.5, 13.7, 12.45,
    #      11.8, 10.87, 9.79, 8.7, 7.7, 6.79, 5.97])  #冬季室外温度
    t_env=temperature*7#环境温度,##########33333333##########应该要爬虫获取
    
    
    probV6=gp.Model("OperatingModelV6")

    ce_h=probV6.addVar(vtype=GRB.CONTINUOUS,name=f"ce_h")
    ce_ce=probV6.addVar(vtype=GRB.CONTINUOUS,name=f"ce_ce")
    cer=probV6.addVar(vtype=GRB.CONTINUOUS,name=f"cer")
    ce_eo=probV6.addVar(vtype=GRB.CONTINUOUS,name=f"ce_eo")
    

    z_g=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_g{i}") for i in range(period)]
    z_u=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_u{i}") for i in range(period)]
    z_in=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_in{i}") for i in range(period)]
    z_out=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_out{i}") for i in range(period)]
    z_fc=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_fc{i}") for i in range(period)]
    z_fca=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_fca{i}") for i in range(period)]
    z_fcb=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_fcb{i}") for i in range(period)]
    z_fcc=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_fcc{i}") for i in range(period)]
    z_aca=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_aca{i}") for i in range(period)]
    z_acb=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_acb{i}") for i in range(period)]
    z_fcth=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_fcth{i}") for i in range(period)]#燃料电池和热交换器转换开关
    z_stc_ex=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_stc_ex{i}") for i in range(period)]#太阳能集热器-换热器-热水罐”流动标志位
    z_ghp_g=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_ghp_g{i}") for i in range(period)]#地源热泵开热
    z_ghp_q=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_ghp_q{i}") for i in range(period)]#地源热泵开冷
    z_wt=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_wt{i}") for i in range(period)]#热水罐换热开关
    z_ct=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_ct{i}") for i in range(period)]#冷水罐换热开关
    z_el=[probV6.addVar(lb=0,ub=1,vtype=GRB.BINARY,name=f"z_el{i}") for i in range(period)]

    g_fc=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_fc{i}") for i in range(period)]
    g_stc=[probV6.addVar(lb=0,ub=400,vtype=GRB.CONTINUOUS,name=f"g_stc{i}") for i in range(period)]#太阳能集热器防冻液参与换热器换热的热量
    g_eb=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_eb{i}") for i in range(period)]#电锅炉发热
    g_hp=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_hp{i}") for i in range(period)]#空气源热泵发热
    g_ghp=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_ghp{i}") for i in range(period)]#地源热泵发热
    g_sts_ghp=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_sts_ghp{i}") for i in range(period)]#供热模式下埋热管给地源热泵供热
    g_ghp_sts=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_ghp_sts{i}") for i in range(period)]#供冷模式下地源热泵给埋热管供热
    g_sts=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_sts{i}") for i in range(period+1)]#埋热管
    g_sts_in=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_sts_in{i}") for i in range(period)]#埋热管
    g_tube=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_tube{i}") for i in range(period)]#管道
    g_inout=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_inout{i}") for i in range(period)]#热水罐
    g_loss=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"g_loss{i}") for i in range(period)]#热水管损失
    m_b=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"m_b{i}") for i in range(period)]
    m_in=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"m_in{i}") for i in range(period)]
    m_el=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"m_el{i}") for i in range(period)]
    m_fc=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"m_fc{i}") for i in range(period)]
    m_out=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"m_out{i}") for i in range(period)]
    m_tube=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"m_tube{i}") for i in range(period)]#管道中水的质量
    m_q=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"m_q{i}") for i in range(period)]#冷水罐换冷水
    p_g=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_g{i}") for i in range(period)]
    p_u=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_u{i}") for i in range(period)]
    p_fc=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_fc{i}") for i in range(period)]
    p_el=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_el{i}") for i in range(period)]
    p_co=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_co{i}") for i in range(period)]
    p_eb=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_eb{i}") for i in range(period)]#电锅炉
    p_hp=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_hp{i}") for i in range(period)]#空气源热泵
    p_ghp=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_ghp{i}") for i in range(period)]#地源热泵
    p_ghp_g=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_ghp_g{i}") for i in range(period)]#地源热泵热
    p_ghp_q=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_ghp_q{i}") for i in range(period)]#地源热泵冷
    q_hp=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"q_hp{i}") for i in range(period)]#空气源热泵制冷
    q_ghp=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"q_ghp{i}") for i in range(period)]#地源热泵制冷
    q_inout=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"q_inout{i}") for i in range(period)]#冷水罐
    q_loss=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"q_loss{i}") for i in range(period)]#冷水罐损耗
    r_ma=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_ma{i}") for i in range(period)]
    r_mb=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_mb{i}") for i in range(period)]
    r_mc=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_mc{i}") for i in range(period)]
    r_md=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_md{i}") for i in range(period)]
    r_ea=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_ea{i}") for i in range(period)]
    r_eb=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_eb{i}") for i in range(period)]
    r_ec=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_ec{i}") for i in range(period)]
    r_ga=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_ga{i}") for i in range(period)]
    r_gb=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_gb{i}") for i in range(period)]
    r_gc=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_gc{i}") for i in range(period)]
    r_aca=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_aca{i}") for i in range(period)]
    r_acb=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"r_acb{i}") for i in range(period)]
    c_aca=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"c_aca{i}") for i in range(period)]
    c_acb=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"c_acb{i}") for i in range(period)]
    u_el=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"u_el{i}") for i in range(period)]#电解槽中氢气的压强
    u_ht=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"u_ht{i}") for i in range(period)]#储氢罐氢气压强
    t_fc_ex=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_fc_ex{i}") for i in range(period)]#燃料电池热交换给热水罐的水的温度
    t_r=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_r{i}") for i in range (period)]#参与换热前的水
    t_cr=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_cr{i}") for i in range (period+1)]#参与换热前的冷水温
    t_gr=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_gr{i}") for i in range (period)]#参与换热前的冷水温
    t_stc=[probV6.addVar(lb=-50,ub=160,vtype=GRB.CONTINUOUS,name=f"t_stc{i}") for i in range(period+1)]#太阳能集热器防冻液温度
    t_stc_ex=[probV6.addVar(lb=0,ub=90,vtype=GRB.CONTINUOUS,name=f"t_stc_ex{i}") for i in range(period)]#换热后流出换热器的水的温度
    t_eb=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_eb{i}") for i in range(period)]#流出电锅炉的热水水温
    t_wt=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_wt{i}") for i in range(period+1)]#热水罐内的热水温度
    t_env_in=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"t_env_in{i}") for i in range(period)]#室内温度
    t_hp_g=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_hp_g{i}") for i in range(period)]#空气源热泵制热水温
    t_hp_q=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"t_hp_q{i}") for i in range(period)]#空气源热泵制冷水温
    t_ghp_g=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"t_ghp_g{i}") for i in range(period)]#地源热泵制热水温
    t_ghp_q=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"t_ghp_q{i}") for i in range(period)]#地源热泵制冷水温
    t_tube=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_tube{i}") for i in range(period)]#管道温度
    t_ct=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_ct{i}") for i in range (period+1)]#冷水罐内冷水温度
    t_q=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"t_q{i}") for i in range (period)]#冷水罐内换冷温度
    w_fc=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"w_fc{i}") for i in range(period)]#处理fuel cell双线性约束参量
    w_stc_ex=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"w_stc_ex{i}") for i in range(period)]#处理太阳能集热器双线性约束参量V6.5（19）
    w_ht=[probV6.addVar(lb=0,ub=100,vtype=GRB.CONTINUOUS,name=f"w_ht{i}") for i in range(period)]#处理热水罐双线性约束参量V6.5（22）
    w_ht_stc_ex=[probV6.addVar(lb=0,ub=90,vtype=GRB.CONTINUOUS,name=f"w_ht_stc_ex{i}") for i in range(period)]#处理热水罐t_stc_ex双线性约束参量V6.5（28）
    w_ht_fc_ex=[probV6.addVar(lb=0,ub=90,vtype=GRB.CONTINUOUS,name=f"w_ht_fc_ex{i}") for i in range(period)]#处理热水罐t_fc_ex双线性约束参量V6.5（28）
    w_ht_wt=[probV6.addVar(lb=0,ub=90,vtype=GRB.CONTINUOUS,name=f"w_ht_wt{i}") for i in range(period)]#处理热水罐t_wt双线性约束参量V6.5（28）
    e_ce=[probV6.addVar(vtype=GRB.CONTINUOUS,name=f"e_ce{i}") for i in range(period)]
    v_gas=[probV6.addVar(vtype=GRB.CONTINUOUS,name=f"v_gas{i}") for i in range(period)]
    
    m_ht=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"m_ht{i}") for i in range(period+1)]
    p_slack=[probV6.addVar(lb=0,vtype=GRB.CONTINUOUS,name=f"p_slack{i}") for i in range(period+1)]#有时候会因为电太多而infeasible，增加弃电量
    probV6.setObjective(gp.quicksum([p_g[i]*lambda_ele_in[i] for i in range(period)])-gp.quicksum(p_u)*lambda_ele_out+gp.quicksum(m_b)*lambda_h,GRB.MINIMIZE)
    #probV6.addConstr(m_ht[0]==5)#定义初状态
    probV6.addConstr(m_ht[-1]==m_ht[0])#最终状态等于0状态
    
    
    
    for i in range(period):
        probV6.addConstr(z_g[i]+z_u[i]<=1)#(6)式，电网购电或上电V6.5(4)
        probV6.addConstr(p_g[i] <= (isolate[0])*z_g[i]*p_transformer)#（7）V6.5(5)
        probV6.addConstr(p_u[i] <= (isolate[1])*z_u[i]*p_transformer)#（7）
        probV6.addConstr(m_b[i] <= (isolate[2])*z_u[i]*p_transformer)#（7）

        probV6.addConstr(p_g[i] + k_pv*S_pv*r_solar[i] + p_fc[i] == p_slack[i] + p_el[i] + p_u[i] + p_co[i] + ele_load[i] + p_eb[i] + p_hp[i] + p_ghp[i])#（2），发电=用电V6.5(3)
        probV6.addConstr(m_b[i] + m_el[i] + m_out[i] == m_in[i] + m_fc[i])#（5），产氢=耗氢V6.5(2)

        # fuel cell
        probV6.addConstr(p_fc[i] <= z_fc[i] * p_fc_nominal)#（10），Fuel Cell小于额定#V6.5(15)
        probV6.addConstr(p_fc[i] >= z_fc[i] * p_fc_nominal_lower)#V6.5大于上届
        probV6.addConstr(z_fca[i] + z_fcb[i] + z_fcc[i] <= 1)#以下式子不在论文里 好像没有(8)(9)，进行分段线性化
        probV6.addConstr(r_ma[i] >= z_fca[i]*0)
        probV6.addConstr(r_ma[i] <= z_fca[i]*0.3)
        probV6.addConstr(r_mb[i] >= z_fcb[i]*0.3)
        probV6.addConstr(r_mb[i] <= z_fcb[i]*0.7)
        probV6.addConstr(r_mc[i] >= z_fcc[i]*0.7)
        probV6.addConstr(r_mc[i] <= z_fcc[i]*1)
        probV6.addConstr(r_ea[i] >= z_fca[i] * 0)
        probV6.addConstr(r_ea[i] <= z_fca[i] * 0.534)
        probV6.addConstr(r_eb[i] >= z_fcb[i] * 0.534)
        probV6.addConstr(r_eb[i] <= z_fcb[i] * 0.91)
        probV6.addConstr(r_ec[i] >= z_fcc[i] * 0.91)
        probV6.addConstr(r_ec[i] <= z_fcc[i] * 1)
        probV6.addConstr(r_ea[i] == 0*z_fca[i] + 1.78*(r_ma[i] - 0*z_fca[i]))
        probV6.addConstr(r_eb[i] == 0.534*z_fcb[i] + 0.94*(r_mb[i] - 0.3*z_fcb[i]))
        probV6.addConstr(r_ec[i] == 0.91*z_fcc[i] + 0.3*(r_mc[i] - 0.7*z_fcc[i]))
        probV6.addConstr(m_fc[i] == 0.11*(r_ma[i] + r_mb[i] + r_mc[i])*p_fc_nominal)
        probV6.addConstr(p_fc[i] == (r_ea[i] + r_eb[i] + r_ec[i])*p_fc_nominal)
        probV6.addConstr(r_ga[i] >= z_fca[i]*0)
        probV6.addConstr(r_ga[i] <= z_fca[i]*0.21)
        probV6.addConstr(r_gb[i] >= z_fcb[i]*0.21)
        probV6.addConstr(r_gb[i] <= z_fcb[i]*0.619)
        probV6.addConstr(r_gc[i] >= z_fcc[i]*0.619)
        probV6.addConstr(r_gc[i] <= z_fcc[i]*1)
        probV6.addConstr(r_ga[i] == 0*z_fca[i] + 0.7*(r_ma[i] - 0*z_fca[i]))
        probV6.addConstr(r_gb[i] == 0.21*z_fcb[i] + 0.9475*(r_mb[i] - 0.3*z_fcb[i]))
        probV6.addConstr(r_gc[i] == 0.619*z_fcc[i] + 1.27*(r_mc[i] - 0.7*z_fcc[i]))
        probV6.addConstr(g_fc[i] == (r_ga[i] + r_gb[i] + r_gc[i])*p_fc_nominal*2.19)
        probV6.addConstr((r_ea[i] + r_eb[i] + r_ec[i]) >= yita_fc_e_nominal * 0.11*(r_ma[i] + r_mb[i] + r_mc[i]) - M*(p_fc_nominal-p_fc[i]))#额定功率时产电COP等于额定值
        probV6.addConstr((r_ea[i] + r_eb[i] + r_ec[i]) <= yita_fc_e_nominal * 0.11*(r_ma[i] + r_mb[i] + r_mc[i]) + M*(p_fc_nominal-p_fc[i]))
        probV6.addConstr((r_ga[i] + r_gb[i] + r_gc[i])*2.19 >= yita_fc_e_nominal * 0.11*(r_ma[i] + r_mb[i] + r_mc[i]) - M*(p_fc_nominal-p_fc[i]))#额定功率时产热COP等于额定值
        probV6.addConstr((r_ga[i] + r_gb[i] + r_gc[i])*2.19 <= yita_fc_e_nominal * 0.11*(r_ma[i] + r_mb[i] + r_mc[i]) + M*(p_fc_nominal-p_fc[i]))
        probV6.addConstr(t_fc_ex[i] >= t_r[i])#V6.5(16),下同
        probV6.addConstr(c * m_fc_w * (t_fc_ex[i] - t_r[i]) == w_fc[i])#双线性改
        probV6.addConstr(g_fc[i]-M*(1-z_fcth[i]) <= w_fc[i])
        probV6.addConstr(g_fc[i]+M*(1-z_fcth[i]) >= w_fc[i])
        probV6.addConstr(w_fc[i] <= M*z_fcth[i])
        probV6.addConstr(M*w_fc[i] >= z_fcth[i])
        probV6.addConstr(z_fcth[i] * epsilon - M * (1 - z_fcth[i]) <= t_fc - t_fc_ex[i])
        probV6.addConstr(t_fc - t_fc_ex[i] <= M * z_fcth[i] - epsilon * (1-z_fcth[i]))
        
        #solar thermal collector
        probV6.addConstr(c * m_stc * (t_stc[i+1]-t_stc[i]) + miu_stc_loss * A_stc *(t_stc[i]-t_env[i]) + c*m_stc_ex*w_stc_ex[i]/theta_ex == k_stc * S_stc * r_solar[i])#V6.5(19)
        probV6.addConstr(w_stc_ex[i] >= t_stc_ex[i]-t_r[i]-M*(1-z_stc_ex[i]))#双线性处理
        probV6.addConstr(w_stc_ex[i] <= t_stc_ex[i]-t_r[i]+M*(1-z_stc_ex[i]))
        probV6.addConstr(w_stc_ex[i] <= M*z_stc_ex[i])
        probV6.addConstr(z_stc_ex[i] <= M*w_stc_ex[i])
        probV6.addConstr(t_stc_ex[i] >= t_r[i])#V6.5(20)
        probV6.addConstr(c * m_stc_ex * (t_stc_ex[i]-t_r[i]) == g_stc[i])
        probV6.addConstr(t_stc[i]-t_stc_ex[i] <= M*z_stc_ex[i]-epsilon*(1-z_stc_ex[i]))#V6.5(21)
        probV6.addConstr(t_stc[i]-t_stc_ex[i] >= -M*(1-z_stc_ex[i])+epsilon*z_stc_ex[i])

        #Compressor
        probV6.addConstr(p_co[i] == m_in[i]*k_co)#V6.5(8)

        #Electrolyzer
        probV6.addConstr(m_el[i] == p_el[i]*k_el)#(12)电->氢V6.5(6)
        probV6.addConstr(p_el[i] <= p_el_nominal)
        probV6.addConstr(u_el[i] == coeff_el_h2u * m_el[i])#V6.5(7)
        probV6.addConstr(z_el[i] * u_el_lower <= u_el[i])
        #probV6.addConstr(z_el[i] * u_el_upper >= u_el[i])

        #H2 Tank
        probV6.addConstr(z_in[i] + z_out[i] <= 1)#(16)V6.5(9)
        probV6.addConstr(m_in[i] <= z_in[i]*m_inout_upper)#(17)V6.5(10)
        probV6.addConstr(m_out[i] <= z_out[i]*m_inout_upper)#V6.5(11)
        probV6.addConstr(m_ht[i+1] - m_ht[i] == m_in[i] - m_out[i])#V6.5(12)
        probV6.addConstr(u_ht[i] == coeff_ht_h2u * m_ht[i])#V6.5(13)
        probV6.addConstr(u_ht[i] <= u_ht_upper)#V6.5(14)
        #probV6.addConstr(u_ht[i] >= u_ht_lower)

        #Hot Water Tank
        probV6.addConstr(c*m_wt*(t_wt[i+1]-t_wt[i])==g_inout[i]-g_loss[i])#V6.5(22)
        probV6.addConstr(g_inout[i]==c*m_io*w_ht[i])
        probV6.addConstr(w_ht[i]<=t_r[i]-t_wt[i]+M*(1-z_wt[i]))
        probV6.addConstr(w_ht[i]>=t_r[i]-t_wt[i]-M*(1-z_wt[i]))
        probV6.addConstr(w_ht[i]<=M*z_wt[i])
        probV6.addConstr(w_ht[i]*M>=z_wt[i])
        probV6.addConstr(g_loss[i]==miu_loss*A_wt*(t_wt[i]-t_env_in[i]))#V6.5(23)
        probV6.addConstr(t_wt[i]>=T_wt_lower)#V6.5(24)
        probV6.addConstr(t_wt[i]<=T_wt_upper)
        probV6.addConstr(g_stc[i]+g_fc[i]+g_eb[i]+g_hp[i]-g_inout[i]==g_tube[i]+g_sts_in[i])#V6.5(25)
        probV6.addConstr(g_tube[i]+g_sts_in[i]==c*m_tube[i]*(t_tube[i]-t_r[i]))#V6.5(26)
        probV6.addConstr(t_tube[i]>=T_g_lower)
        probV6.addConstr(z_stc_ex[i]*m_stc_ex+z_fcth[i]*m_fc_w+m_eb+m_hp_g+z_wt[i]*m_io==m_tube[i])#V6.5(27)
        probV6.addConstr(m_stc_ex*w_ht_stc_ex[i]+m_fc_w*w_ht_fc_ex[i]+m_eb*t_eb[i]+m_hp_g*t_hp_g[i]+m_io*w_ht_wt[i]==m_tube[i]*t_tube[i])#V6.5(28)
        probV6.addConstr(w_ht_stc_ex[i]<=t_stc_ex[i]+M*(1-z_stc_ex[i]))#w_ht_stc_ex
        probV6.addConstr(w_ht_stc_ex[i]>=t_stc_ex[i]-M*(1-z_stc_ex[i]))
        probV6.addConstr(w_ht_stc_ex[i]<=M*z_stc_ex[i])
        probV6.addConstr(w_ht_stc_ex[i]*M>=z_stc_ex[i])
        probV6.addConstr(w_ht_fc_ex[i]<=t_fc_ex[i]+M*(1-z_fcth[i]))#w_ht_fc_ex
        probV6.addConstr(w_ht_fc_ex[i]>=t_fc_ex[i]-M*(1-z_fcth[i]))
        probV6.addConstr(w_ht_fc_ex[i]<=M*z_fcth[i])
        probV6.addConstr(w_ht_fc_ex[i]*M>=z_fcth[i])
        probV6.addConstr(w_ht_wt[i]<=t_wt[i]+M*(1-z_wt[i]))#w_ht_wt
        probV6.addConstr(w_ht_wt[i]>=t_wt[i]-M*(1-z_wt[i]))
        probV6.addConstr(w_ht_wt[i]<=M*z_wt[i])
        probV6.addConstr(w_ht_wt[i]*M>=z_wt[i])
        
        #Cold Water Tank
        probV6.addConstr(c*m_ct*(t_ct[i]-t_ct[i+1])==q_inout[i]-q_loss[i])#V6.5(41)
        probV6.addConstr(q_inout[i]==z_ct[i]*c*m_cio*(t_ct[i]-t_cr[i]))
        probV6.addConstr(q_loss[i]==miu_loss*A_ct*(t_env_in[i]-t_ct[i]))#V6.5(42)
        probV6.addConstr(t_ct[i]<=T_ct_upper)#V6.5(43)
        probV6.addConstr(t_ct[i]>=T_ct_lower)
        probV6.addConstr(q_ghp[i]+q_hp[i]-q_inout[i]==q_demand[i])#V6.5(44)
        probV6.addConstr(q_demand[i]<=c*m_q[i]*(t_cr[i]-t_q[i]))
        probV6.addConstr(t_q[i]<=T_q_lower)
        probV6.addConstr(m_hp_q+m_ghp_q+z_ct[i]*m_cio==m_q[i])#V6.5(45)
        probV6.addConstr(m_hp_q*t_hp_q[i]+m_ghp_q*t_ghp_q[i]+z_ct[i]*m_cio*t_ct[i]==m_q[i]*t_q[i])#V6.5(46)
        
        
        #Electric boiler
        probV6.addConstr(c*m_eb*(t_eb[i] - t_r[i]) == k_eb*p_eb[i])#V6.5(29)
        probV6.addConstr(p_eb[i] <= p_eb_nominal)
        probV6.addConstr(g_eb[i] == k_eb*p_eb[i])
        
        #空气源热泵
        probV6.addConstr(c * m_hp_g * (t_hp_g[i]-t_r[i]) == yita_hp_g*p_hp[i])#V6.5(30)
        probV6.addConstr(p_hp[i]<=p_hp_nominal)
        probV6.addConstr(g_hp[i] <= yita_hp_g*p_hp[i])
        probV6.addConstr(c * m_hp_q * (t_cr[i]-t_hp_q[i]) == yita_hp_q*p_hp[i])#V6.5(31)
        probV6.addConstr(q_hp[i] == yita_hp_q*p_hp[i])
        
        #地源热泵
        probV6.addConstr(c*m_ghp_g*(t_ghp_g[i]-t_gr[i])==yita_ghp_g*p_ghp_g[i])#V6.5(32)
        probV6.addConstr(g_ghp[i]==yita_ghp_g*p_ghp_g[i])
        probV6.addConstr(p_ghp_g[i]<=z_ghp_g[i]*p_ghp_nominal)
        probV6.addConstr(c*m_ghp_q*(t_cr[i]-t_ghp_q[i])==yita_ghp_q*p_ghp_q[i])#V6.5(33)
        probV6.addConstr(q_ghp[i]==yita_ghp_q*p_ghp_q[i])
        probV6.addConstr(p_ghp_q[i]<=z_ghp_q[i]*p_ghp_nominal)
        probV6.addConstr(p_ghp_q[i]+p_ghp_g[i]==p_ghp[i])#V6.5(34)
        probV6.addConstr(z_ghp_g[i]+z_ghp_q[i]<=1)
        probV6.addConstr(g_sts_ghp[i]==g_ghp[i]*(1-1/yita_ghp_g))#V6.5(35)
        probV6.addConstr(g_ghp_sts[i]==q_ghp[i]*(1+1/yita_ghp_q))#V6.5(36)
        
        #埋热管
        probV6.addConstr(g_sts[i+1]-g_sts[i]==g_ghp_sts[i]-g_sts_ghp[i]+g_sts_in[i])#V6.5(39)
        
        #供热
        g_tube[i]+g_ghp[i]>=g_demand[i]#V6.5(40)
        
        probV6.addConstr(e_ce[i]==ele_load[i])
        probV6.addConstr(v_gas[i]==(g_demand[i]+q_demand[i]/1.35)/7.5)

    probV6.addConstr(ce_h==gp.quicksum(m_b)*alpha_H2+gp.quicksum(p_g)*alpha_e)#V6.5(47)
    probV6.addConstr(ce_ce==gp.quicksum(e_ce)*alpha_e+gp.quicksum(v_gas)*alpha_gas)#V6.5(48)
    probV6.addConstr(cer==ce_ce-ce_h)#V6.5(49)
    probV6.addConstr(ce_eo==gp.quicksum(p_u)*alpha_eo)#V6.5(50)
    
    print("It has reached here")
    
    probV6.params.NonConvex = 2
    probV6.params.MIPGap = 0.05

    try:
        probV6.optimize()
    except gp.GurobiError:
        print("Optimize failed due to non-convexity")
        
    print(probV6.status)
    print("----")
    #input()
    if probV6.status == GRB.INFEASIBLE or probV6.status == 4:
        print('Model is infeasible111')
        return 1,1,1,1
        probV6.computeIIS()
        probV6.write('model.ilp')
        print("Irreducible inconsistent subsystem is written to file 'model.ilp'")
        
    #prob.solve(pulp.GUROBI_CMD(options=[('MIPgap',0.0001)]))

    #print('status:', pulp.LpStatus[prob.status])

    res=   {'objective':probV6.objVal,
            'process time':time.time() - t0,
            'ce_h':ce_h.X,
            'cer':cer.X,
            'ele_load':dict_load['ele_load'],
            'g_demand':dict_load['g_demand'],
            'q_demand': dict_load['q_demand'],
            'r_solar':dict_load['r_solar'],
            'lambda_ele_in':lambda_ele_in,
            'z_g':[z_g[i].X for i in range(period)],
            'z_u':[z_u[i].X for i in range(period)],
            'z_in':[z_in[i].X for i in range(period)],
            'z_out':[z_out[i].X for i in range(period)],
            'g_fc':[g_fc[i].X for i in range(period)],
            'm_b':[m_b[i].X for i in range(period)],
            'm_in':[m_in[i].X for i in range(period)],
            'm_el':[m_el[i].X for i in range(period)],
            'm_fc':[m_fc[i].X for i in range(period)],
            'm_out':[m_out[i].X for i in range(period)],
            'p_g':[p_g[i].X for i in range(period)],
            'p_u':[p_u[i].X for i in range(period)],
            'p_fc':[p_fc[i].X for i in range(period)],
            'p_el':[p_el[i].X for i in range(period)],
            'p_co':[p_co[i].X for i in range(period)],
            'm_ht':[m_ht[i].X for i in range(period+1)],
            }
    opex=probV6.objVal
    #print(ce_h.X,opex,res)
    #exit(0)
    return ce_h.X,opex,res,0

def operating_problem(dict_load,device_cap,isolate,tem_env,input_json,period):
    # isloate 0表示并网，1表示离网
    area = input_json['load']['load_area']#总面积
    #参数先常数

    #第一步，计算 传统 电气系统 和 电系统 的 运行成本， 碳排放
    gas_price = 1.2
    lambda_ele_in = input_json['price']['TOU_power']*365
    ele_sum_ele_only=np.array(dict_load['ele_load'])+np.array(dict_load['g_demand'])/input_json['device']['eb']['beta_eb']+np.array(dict_load['q_demand'])/input_json['device']['hp']['beta_hpq']
    gas_sum_ele_gas=(np.array(dict_load['g_demand'])+np.array(dict_load['q_demand'])/1.35)/7.5
    opex_ele_only=sum(np.array(lambda_ele_in)*ele_sum_ele_only)
    opex_ele_gas=sum(np.array(lambda_ele_in)*np.array(dict_load['ele_load']))+sum(gas_sum_ele_gas*gas_price)
    co2_ele_only=sum(ele_sum_ele_only)*input_json['carbon']['alpha_e']
    co2_ele_gas=sum(dict_load['ele_load'])*input_json['carbon']['alpha_e']+sum(gas_sum_ele_gas)*1.535

    #分别算四个季节的运行程序，得到碳排放和运行成本，算一个一年的运行成本和碳排放。
    dict_spring={'ele_load':dict_load['ele_load'][3288:3288+7*24],'g_demand':dict_load['g_demand'][3288:3288+7*24],'q_demand':dict_load['q_demand'][3288:3288+7*24],'r_solar':dict_load['r_solar'][3288:3288+7*24]}
    dict_summer={'ele_load':dict_load['ele_load'][6192:6192+7*24],'g_demand':dict_load['g_demand'][6192:6192+7*24],'q_demand':dict_load['q_demand'][6192:6192+7*24],'r_solar':dict_load['r_solar'][6192:6192+7*24]}
    dict_autumn={'ele_load':dict_load['ele_load'][7656:7656+7*24],'g_demand':dict_load['g_demand'][7656:7656+7*24],'q_demand':dict_load['q_demand'][7656:7656+7*24],'r_solar':dict_load['r_solar'][7656:7656+7*24]}
    dict_winter={'ele_load':dict_load['ele_load'][360:360+7*24],'g_demand':dict_load['g_demand'][360:360+7*24],'q_demand':dict_load['q_demand'][360:360+7*24],'r_solar':dict_load['r_solar'][360:360+7*24]}

    ce_h_spring,opex_spring,res_spring,flag1 = season_operating_problem(dict_spring,device_cap,isolate,tem_env,input_json,7*24)
    ce_h_summer,opex_summer,res_summer,flag2 = season_operating_problem(dict_summer,device_cap,isolate,tem_env,input_json,7*24)
    ce_h_autumn,opex_autumn,res_autumn,flag3 = season_operating_problem(dict_autumn,device_cap,isolate,tem_env,input_json,7*24)
    ce_h_winter,opex_winter,res_winter,flag4 = season_operating_problem(dict_winter,device_cap,isolate,tem_env,input_json,7*24)
    print(flag1,flag2,flag3,flag4)
    #exit(0)
    if flag1 == 1 or flag2 == 1 or flag3 ==1 or flag4 ==1:
        return 0,1
    opex_sum=(opex_spring+opex_summer+opex_autumn+opex_winter)*12
    ce_sum=(ce_h_spring+ce_h_summer+ce_h_autumn+ce_h_winter)*12
    
    #第三步算结果
    output_json = {
            "operation_cost": format(opex_sum,'.2f'),  # 年化运行成本/万元
            "cost_save_rate": format((opex_ele_only-opex_sum)/opex_ele_only,'.4f'),  #电运行成本节约比例
            "cost_save_rate_gas": format((opex_ele_gas-opex_sum)/opex_ele_gas,'.4f'),  #电气运行成本节约比例
            "co2":format(ce_sum,'.2f'),  #总碳排/t
            "cer_rate":format((co2_ele_only-ce_sum)/co2_ele_only,'.4f'),  #与电系统相比的碳减排率
            "cer_gas":format((co2_ele_gas-ce_sum)/co2_ele_gas,'.4f'), #与电气系统相比的碳减排率
            "cer_perm2":format((co2_ele_only-ce_sum)/area,'.2f'),  #电系统每平米的碳减排量/t
            "cer_perm2_gas":format((co2_ele_gas-ce_sum)/area,'.2f'),  #电气系统每平米的碳减排量/t
            "cer":format(co2_ele_only-ce_sum,'.4f')
    }

    return output_json,0
