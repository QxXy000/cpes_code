import json

with open("grid_planning_output_json.json",encoding = "utf-8") as load_file:
    grid_planning_output_json = json.load(load_file)
with open("grid_operation_output_json.json",encoding = "utf-8") as load_file:
    grid_operation_output_json = json.load(load_file)
with open("itgrid_planning_output_json.json",encoding = "utf-8") as load_file:
    itgrid_planning_output_json = json.load(load_file)
with open("itgrid_operation_output_json.json",encoding = "utf-8") as load_file:
    itgrid_operation_output_json = json.load(load_file)