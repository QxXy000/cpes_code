# cpes_code

通过`main_input.json`进行配置，运行`main.py`进行计算
# 输入配置文件说明
配置文件包`main_input.json`。具体配置说明如下。


## 详细配置文件

### 负荷部分

输入三部分内容，第一部分`load_area`为数组，分别待变电热冷的供应面积；第二部分`load_sum_up`为数组，代表全年电热冷负荷的总量。前项为必备数据。第三项为8760负荷数据文件，`detail_load`中填入文件路径。
```
    "load":{
        "load_sort":1,
        "building_area":{
            "apartment":0,
            "hotel":0,
            "office":1,
            "restaurant":0
        },
        "park_area":[1,2,3,4,5],
        "power_peak":0,
        "yearly_power":0,
        "load_area":12000,
        "load_proportion":{
            "ele":0,
            "heat":0,
            "cold":0
        },
        "location":[112,16],
        "detail_load":"load.csv"
    },
```

### 可再生能源部分

第一项`location`为测算经纬度，输入项目所在地经纬度，用于获取当地光照水平；第二项`pv_existst`为已有光伏装机容量功率；第三项`pv_max`为最大光伏规划面积；第四项`beta_pv`为光伏板效率；第五项`sc_existst`为已有的太阳能集热器面积；第六项`sc_max`为允许对打的集热器面积；第七项`pv_sc_max`为光伏板和集热器一共的最大面积。
```
    "renewable_energy":{

        "pv_existst":1000,
        
        "sc_existst":1000,
        "pv_sc_max":100000
    },
```

### 市场价格部分

第一项`TOU_power`为数组，代表24h分时电价，第二项`power_sale`为卖电价格；第三项`heat_price`为供热价格，单位是元/平方米；第四项`cold_price`为供冷价格；第五项`hydrogen_price`为氢价，单位是元/kg。
```
    "price":{
        "TOU_power":[0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.7, 
            1, 1, 1, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 1.2, 1.2, 1.2, 1.2, 1.2, 0.4],
        //分时电价，提供24小时
        "power_sale":0.5,
        //卖电价格
        "heat_price":100,
        //供热价格，元/平方米
        "cold_price":100,
        //供冷价格，元/名方米
        "hydrogen_price":20,
        //氢价（元/kg）
    },

```

### 设备部分

设备包括氢能系统设备和水循环供热系统设备。

el代表电解槽设备，`power_max`代表最大规划容量，`power_min`代表最小规划容量，`cost`代表设备单价，元/kwh，`crf`代表设备寿命。
运行参数中`beta_el`代表电解槽制氢效率，`500RtV`代表输出氢气质量压强换算系数，`U_max,U_min`代表输出压强上下限。
```
	"el"://电解槽
	    {
	        "power_max":500,
	        //最大规划容量
	        "power_min":0,
	        //最小规划容量
	        "cost":12000,
	        //设备单价
	        "crf":7,
	        //设备寿命

	        //运行参数
	        "beta_el":0.03,
	        //制氢效率
	        "500RtV":0,
	        //输出氢气质量压强换算系数
	        "U_max":200,
	        "U_min":20,
	        //输出压强上下限
	    },
```

co代表压缩机设备，`power_max`代表最大规划容量，`power_min`代表最小规划容量，`cost`代表设备单价，元/kwh，`crf`代表设备寿命。
运行参数中`beta_co`代表氢压机功耗。
```
    "co":
        {
            "power_max":5000,
            "power_min":0,
            "cost":1000,
            "crf":10,

            "beta_co":1.399
        },
```
hst代表储氢罐`sto_max`代表最大规划容量,`inout_max`代表单位时间最大进出氢气量,`cost`代表设备单价，元/kwh，`crf`代表设备寿命。`U_max,U_min`代表压强上下限。
```
	"hst"://储氢罐
	    {
	        "sto_max":5000,
	        //最大容量
	        "stp_min":0,
	        //最小规划容量
	        "cost":1791,
	        //设备单价
	        "crf":10,
	        //设备寿命

	        //运行参数
	        "inout_max":500,
	        //最大进出量
	        "U_max":350,
	        "U_min":5,
	        //储氢罐压强上下限
	    },
```

fc代表燃料电池设备，`power_max`代表最大规划容量，`power_min`代表最小规划容量，`cost`代表设备单价，元/kwh，`crf`代表设备寿命。
运行参数中`eta_fc_p`代表产电效率，`eta_ex_g`代表制热效率，`theta_ex`代表换热效率。
```
	"fc"://燃料电池热电联产unit
	    {
	        "power_max":10000,
	        //最大规划容量
	        "power_min":0,
	        //最小规划容量
	        "cost":12000,
	        //设备单价
	        "crf":7,
	        //设备寿命

	        //运行参数
	        "eta_fc_p":15,
	        //产电效率kwh/kg
	        "eta_ex_g":16.6,
	        //制热效率kwg/kg
	        "theta_ex":0.95,
	        //换热效率

	    },
```

sc代表太阳能集热器，`cost`代表设备单价，元/kwh，`crf`代表设备寿命。运行参数中`beta_sc`代表效率，`miu_loss`代表损失率，`theta_ex`代表换热效率。

```
    "sc"://太阳能集热器
        {
            "area_max":10000,
            //最大规划容量
            "area_min":0,
            //最小规划容量
            "cost":2000,
            //设备单价
            "crf":20,
            //设备寿命

            //运行参数
            "beta_sc":0.55,
            //集热器效率
            "theta_ex":0.9,
            //换热效率
            "miu_loss":0.9,
            //损失率
        },

```
ht代表热水罐，ct代表冷水罐，`water_max`和`water_min`代表最大最小规划容量`cost`代表设备单价，元/kwh，`crf`代表设备寿命。
运行参数中`t_max`，`t_min`代表最大最小水罐温度，`t_supply`代表最小供热温度和最大供冷温度，`miu_loss`代表损失率，`theta_ex`代表换热效率。

```
    "ht"://热水罐
        {
            "water_max":10000,
            //最大规划容量
            "water_min":0,
            //最小规划容量
            "cost":2000,
            //设备单价
            "crf":20,
            //设备寿命

            //运行参数
            "t_max":82,
            //最高水温
            "t_min":4,
            //最低水温
            "t_supply":55,
            //最低供热温度
            "miu_loss":0.02,
            //损失率m2.K
        },
    "ct"://冷水罐
        {
            "water_max":10000,
            //最大规划容量
            "water_min":0,
            //最小规划容量
            "cost":2000,
            //设备单价
            "crf":20,
            //设备寿命

            //运行参数
            "t_max":21,
            //最高水温
            "t_min":4,
            //最低水温
            "t_supply":7,
            //最低水温
            "miu_loss":0.9,
            //损失率
        },
```

eb代表电热锅炉设备，`power_max`代表最大规划容量，`power_min`代表最小规划容量，`cost`代表设备单价，元/kwh，`crf`代表设备寿命。`beta_eb`代表产热效率。

```
    "eb"://电热锅炉
        {
            "power_max":10000,
            //最大规划容量
            "power_min":0,
            //最小规划容量
            "cost":2000,
            //设备单价
            "crf":20,
            //设备寿命

            //运行参数
            "beta_eb":0.8,
            //产热效率
        },
```
hp代表空气源热泵设备，`power_max`代表最大规划容量，`power_min`代表最小规划容量，`cost`代表设备单价，元/kwh，`crf`代表设备寿命。`beta_hpg`代表产热COP，`beta_hpq`代表制冷COP。

```
    "hp"://空气源热泵
        {
            "power_max":10000,
            //最大规划容量
            "power_min":0,
            //最小规划容量
            "cost":2000,
            //设备单价
            "crf":20,
            //设备寿命

            //运行参数
            "beta_hpg":3,
            //产热效率
            "beta_hpq":4,
            //制冷效率
        },
```

ghp代表地源热泵设备，`power_max`代表最大规划容量，`power_min`代表最小规划容量，`cost`代表设备单价，元/kwh，`crf`代表设备寿命。`beta_ghpg`代表产热COP，`beta_ghpq`代表制冷COP。
```
    "ghp"://地源热泵
        {
            "power_max":10000,
            //最大规划容量
            "power_min":0,
            //最小规划容量
            "cost":2000,
            //设备单价
            "crf":20,
            //设备寿命

            //运行参数
            "beta_ghpg":3.4,
            //产热效率
            "beta_ghpq":3.4,
            //制冷效率
        },
```

### 运行模式部分

`optimal`,`storage`,`isloate`分别代表最优，储能消纳和离网模式。其中储能消纳模式需要参数`sigma`代表储能消纳比例，`supply_time`代表储能可以供应负荷的持续时间，`pv_time`代表消纳光伏的时间。
```
    "mode":{
        //运算模式
        "optimal":1,
        "storage":{
            "select":1,
            //是否选择本模式
            "sigma":0.1,
            //储能比例
            "supply_time":4,
            //供应负荷持续时间
            "pv_time":4,
            //消纳光伏时间
        },
        "isloate":1,
        //0代表不算，1代表只计算规划模型，2代表规划和运行模型一并计算
    },
```


### 碳排放参数

```
    "carbon":{
        //碳排放因子
        "alpha_h2":1.74,
        //氢气排放因子
        "alpha_e":0.5839,
        //电网排放因子kg/kwh
        "alpha_EO":0.8922,
        //减排项目基准排放因子
    }
```
