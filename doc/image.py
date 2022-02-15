import matplotlib.pyplot as plt
from matplotlib.pyplot import MultipleLocator
from output import *
def light_image():
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(5.85,3.49),dpi=100)
    plt.ylabel(u'光照强度(kw/m2)',fontsize=10)
    plt.xticks(fontproperties = 'Times New Roman', size = 10)
    plt.yticks(fontproperties = 'Times New Roman', size = 10)
    plt.plot(grid_planning_output_json['r_solar'],color='orange',alpha=1)
    plt.xlim(0,len(grid_planning_output_json['r_solar'])+1)
    plt.ylim(0,1.)
    #设置刻度间隔
    x_major_locator=MultipleLocator(24*30)
    y_major_locator=MultipleLocator(0.1)
    ax=plt.gca()
    ax.xaxis.set_major_locator(x_major_locator)
    ax.yaxis.set_major_locator(y_major_locator)
    plt.title(u"全年光照强度图",fontsize=14)
    # plt.show()
    plt.savefig('.\docx\word\media\image2.png')
def load_image():
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(7.13, 4.43), dpi=100)
    plt.ylabel(u'负荷(kW·h)', fontsize=10)
    plt.xticks(fontproperties='Times New Roman', size=10)
    plt.yticks(fontproperties='Times New Roman', size=10)
    plt.plot(grid_planning_output_json['ele_load'], color='blue', alpha=1,label=u'电负荷',linewidth=2)
    plt.plot(grid_planning_output_json['g_demand'], color='orange', alpha=1,label=u'热负荷',linewidth=2)
    plt.plot(grid_planning_output_json['q_demand'], color='gray', alpha=1,label=u'冷',linewidth=2)
    plt.xlim(0, len(grid_planning_output_json['ele_load']) + 1)
    plt.ylim(0,)
    # 设置刻度间隔
    x_major_locator = MultipleLocator(24 * 30)
    ax = plt.gca()
    ax.xaxis.set_major_locator(x_major_locator)
    plt.grid(linewidth=0.7,axis='y')
    plt.title(u"全年电热冷负荷图", fontsize=14)
    plt.legend()
    plt.savefig('.\docx\word\media\image3.png')
