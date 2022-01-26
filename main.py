
import gurobipy as gp
from gurobipy import GRB
import numpy as np
import xlwt
import xlrd
import random
import time
import csv
from chicken_plan import *
from chicken_op import *
import json
import os

def read_load_file(filename):
    ele_load = [0 for i in range(8760)]
    g_demand = [0 for i in range(8760)]
    q_demand = [0 for i in range(8760)]
    r_solar =  [0 for i in range(8760+24)]
    with open("load/"+filename) as officecsv:

        office = csv.DictReader(officecsv)
        i=0
        for row in office:
            ele_load[i] += float(row['Electricity Load [J]'])
            q_demand[i] += float(row['Cooling Load [J]'])
            g_demand[i] += float(row['Heating Load [J]'])
            
            i+=1
    print(sum(g_demand),sum(q_demand),sum(ele_load))
    return ele_load,g_demand,q_demand

def get_load_new(load_dict):

    load_apartment = "ApartmentMidRise.csv"
    load_hotel     = "HotelSmall.csv"
    load_office    = "OfficeMedium.csv"
    load_restaurant= "RestaurantSitDown.csv"
    if load_dict["load_sort"] == 1:
        load_apartment  = "Heilongjiang_Harbin_"+load_apartment  
        load_hotel      = "Heilongjiang_Harbin_"+load_hotel      
        load_office     = "Heilongjiang_Harbin_"+load_office     
        load_restaurant = "Heilongjiang_Harbin_"+load_restaurant 
    if load_dict["load_sort"] == 2:
        load_apartment  = "Hebei_Shijiazhuang_"+load_apartment  
        load_hotel      = "Hebei_Shijiazhuang_"+load_hotel      
        load_office     = "Hebei_Shijiazhuang_"+load_office     
        load_restaurant = "Hebei_Shijiazhuang_"+load_restaurant 

    if load_dict["load_sort"] == 3:
        load_apartment  = "Jiangsu_Nanjing_"+load_apartment  
        load_hotel      = "Jiangsu_Nanjing_"+load_hotel      
        load_office     = "Jiangsu_Nanjing_"+load_office     
        load_restaurant = "Jiangsu_Nanjing_"+load_restaurant 
    if load_dict["load_sort"] == 4:
        load_apartment  = "Hainan_Haikou_"+load_apartment  
        load_hotel      = "Hainan_Haikou_"+load_hotel      
        load_office     = "Hainan_Haikou_"+load_office     
        load_restaurant = "Hainan_Haikou_"+load_restaurant 
    if load_dict["load_sort"] == 5:
        load_apartment  = "Yunnan_Kunming_"+load_apartment  
        load_hotel      = "Yunnan_Kunming_"+load_hotel      
        load_office     = "Yunnan_Kunming_"+load_office     
        load_restaurant = "Yunnan_Kunming_"+load_restaurant 
    # print(load_apartment )
    # print(load_hotel     )
    # print(load_office    )
    # print(load_restaurant)
    # exit(0)
    e1,g1,q1 = read_load_file(load_apartment)
    e2,g2,q2 = read_load_file(load_hotel)
    e3,g3,q3 = read_load_file(load_office)
    e4,g4,q4 = read_load_file(load_restaurant)
    #print(load_dict["load_sort"]["building_area"])
    sum_rate = load_dict["building_area"]["apartment"]+load_dict["building_area"]["hotel"]+load_dict["building_area"]["office"]+load_dict["building_area"]["restaurant"]
    rate1 = load_dict["load_area"]*load_dict["building_area"]["apartment"]/sum_rate
    rate2 = load_dict["load_area"]*load_dict["building_area"]["hotel"]/sum_rate
    rate3 = load_dict["load_area"]*load_dict["building_area"]["office"]/sum_rate
    rate4 = load_dict["load_area"]*load_dict["building_area"]["restaurant"]/sum_rate
    ele_load =  [e1[i]*rate1+e2[i]*rate2+e3[i]*rate3+e4[i]*rate4 for i in range(len(e1))]
    g_demand = [g1[i]*rate1+g2[i]*rate2+g3[i]*rate3+g4[i]*rate4 for i in range(len(e1))]
    q_demand = [q1[i]*rate1+q2[i]*rate2+q3[i]*rate3+q4[i]*rate4 for i in range(len(e1))]
    q_demand[:92*24] = [0 for i in range(92*24)]
    q_demand[-61*24:] = [0 for i in range(61*24)]
    g_demand[92*24:92*24+212*24] = [0 for i in range(212*24)]
    period = len(e1)
    min_err = 10000
    files=os.listdir(r'solar')

    for file in files:
        #for i in range(len(df)):
        lon=file.split('_')[2]
        lat=file.split('_')[3]
        # print(((float(lat)-float(df.iloc[:,2][i]))**2+(float(lon)-float(df.iloc[:,3][i]))**2))
        #print(load_dict["location"])
        err = (float(lat)-float(load_dict["location"][0]))**2+(float(lon)-float(load_dict["location"][1]))**2
        if err<min_err:
            min_err = err
            final_file = file
        #print(float(lat),float(lon))
        #print(err,min_err)
    #print(final_file,min_err)
    r_solar =  [0 for i in range(8760+24)]
    with open("solar/"+final_file) as renewcsv:
        renewcsv.readline()
        renewcsv.readline()
        renewcsv.readline()
        renew = csv.DictReader(renewcsv)
        
        i=0
        for row in renew:

            r_solar[i] += float(row['electricity'])
            i+=1

    if load_dict["yearly_power"] !=0:
        #print(1)
        tmp_sum = sum(ele_load)+sum(q_demand)/4+sum(g_demand)/0.95
        kkk = load_dict["yearly_power"] /tmp_sum
        g_demand = [g_demand[i]*kkk for i in range(period)]
        q_demand = [q_demand[i]*kkk for i in range(period)]
        ele_load = [ele_load[i]*kkk for i in range(period)]
    print(max(g_demand),max(q_demand),max(ele_load))
    print(sum(g_demand),sum(q_demand),sum(ele_load))
    dict_load = {'ele_load': ele_load, 'g_demand': g_demand, 'q_demand': q_demand, 'r_solar': r_solar}
    #exit(0)
    return dict_load

def get_load():
    period = 8760

    #book_spr = xlrd.open_workbook('cspringdata.xlsx')
    #book_sum = xlrd.open_workbook('csummerdata.xlsx')
    #book_aut = xlrd.open_workbook('cautumndata.xlsx')
    #book_win = xlrd.open_workbook('cwinterdata.xlsx')

    

    #print(len(r_solar),len(t_env_indoor),len(t_env_outdoor))
    #print(max(r_solar))
    #exit(0)
    # book = xlrd.open_workbook('new_xls.xlsx')
    # data = book.sheet_by_index(0)
    # for l in range(1,8761):
    #     q_demand.append(data.cell(l,1).value)
    #     g_demand.append(data.cell(l,2).value)
    #     m_demand.append(data.cell(l,3).value)
    #     ele_load.append(data.cell(l,4).value)
    # q_demand = [0 if num == '' else num for num in q_demand]
    # g_demand = [0 if num == '' else num for num in g_demand]
    # m_demand = [0 if num == '' else num for num in m_demand]
    # ele_load = [0 if num == '' else num for num in ele_load]
    #print(q_demand)
    #exit(0)
    # for l in range(1,8761):
    #     q_demand.append(float(data.cell(l,1).value))
    #     g_demand.append(float(data.cell(l,2).value))
    #     m_demand.append(float(data.cell(l,3).value)/(30*c))
    #     ele_load.append(float(data.cell(l,4).value))
    ele_load = [0 for i in range(8760)]
    g_demand = [0 for i in range(8760)]
    q_demand = [0 for i in range(8760)]
    r_solar =  [0 for i in range(8760+24)]
    with open('load.csv') as officecsv:

        office = csv.DictReader(officecsv)
        i=0
        for row in office:
            ele_load[i] += float(row['Electricity Load [J]'])
            q_demand[i] += float(row['Cooling Load [J]'])
            g_demand[i] += float(row['Heating Load [J]'])
            
            i+=1
    print(sum(g_demand),sum(q_demand),sum(ele_load))
    #book = xlrd.open_workbook('renewable.csv')
    with open('renewable1.csv') as renewcsv:
        renewcsv.readline()
        renewcsv.readline()
        renewcsv.readline()
        renew = csv.DictReader(renewcsv)
        
        i=0
        for row in renew:

            r_solar[i] += float(row['radiation_surface'])
            i+=1
    #print(r_solar)
    q_demand[:92*24] = [0 for i in range(92*24)]
    q_demand[-61*24:] = [0 for i in range(61*24)]
    g_demand[92*24:92*24+212*24] = [0 for i in range(212*24)]
    r_solar = r_solar[-8:]+r_solar[:-8]
    r_solar = [r_solar[i]/1000 for i in range(period)]

    kkk = 12000
    tmp_sum = sum(ele_load)+sum(q_demand)/4+sum(g_demand)/0.95
    kkk2 = 10000000/tmp_sum
    g_demand = [g_demand[i]*kkk for i in range(period)]
    q_demand = [q_demand[i]*kkk for i in range(period)]
    ele_load = [ele_load[i]*kkk for i in range(period)]
    #print(max(g_demand),max(q_demand),max(ele_load))
    #print(sum(g_demand),sum(q_demand),sum(ele_load))
    #exit(0)
    #s_e = sum(ele_load)
    #s_s = sum(r_solar)
    #ele_load = [ele_load[i]*4971355/s_e for i in range(period)]
    #g_demand = [g_demand[i] for i in range(period)]
    #q_demand = [q_demand[i] for i in range(period)]
    #r_solar = [r_solar[i]*1362/s_s for i in range(period)]
    print(max(g_demand),max(q_demand),max(ele_load))
    print(sum(g_demand),sum(q_demand),sum(ele_load))
    # print(len(r_solar))
    # exit(0)

    dict_load = {'ele_load': ele_load, 'g_demand': g_demand, 'q_demand': q_demand, 'r_solar': r_solar}
    return dict_load

def to_csv(res,filename):
    items = list(res.keys())
    wb = xlwt.Workbook()
    total = wb.add_sheet('garden')
    for i in range(len(items)):
        total.write(0,i,items[i])
        if type(res[items[i]]) == list:
            sum = 0
            print(items[i])
            for j in range(len(res[items[i]])):
                total.write(j+2,i,(res[items[i]])[j])
                # sum += (res[items[i]])[j]
            # total.write(1,i,sum)
        else:
            total.write(1,i,res[items[i]])

    #filename = 'res/chicken_plan_2_load_1' + '.xls'
    wb.save(filename)



if __name__ == '__main__':

    
    #exit(0)
    with open("main_input.json",encoding = "utf-8") as load_file:
        input_json = json.load(load_file)

    #dict_load = get_load()
    dict_load = get_load_new(input_json["load"])

    #exit(0)
    #res1,grid_output_json,grid_operation_output_json,device_cap1 = planning_problem(dict_load, 0, input_json)
    #print(output_json,operation_output_json)
    output_json = operating_problem(dict_load, 1,0,0,input_json,8760)
    print(output_json)
    exit(0)
    res2,isloat_output_json,isloate_operation_output_json,device_cap2 = planning_problem(dict_load, 1, input_json)
    print(device_cap1,device_cap2)
    print(grid_operation_output_json,isloate_operation_output_json)
    #output_json = operating_problem(dict_load, device_cap, 1, tmp_env, input_json)

    #output_json = operating_problem(dict_load, device_cap, 0, tmp_env, input_json)

    


    to_csv(res1,'test1' + '.xls')
    to_csv(res2,'test2' + '.xls')

