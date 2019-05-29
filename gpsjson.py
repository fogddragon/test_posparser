import json
from datetime import datetime
import geojson
import os
import subprocess


def read_json_file(path):
    with open(path) as file:
        raw_json = file.read()
    return json.loads(raw_json)


def read_pos_file(path):
    pos = []
    with open(path) as file:
        for line in file:
            if line.startswith('%'):
                continue
            line_data = line.split('  ')
            pos.append({
                'GPST':  datetime.strptime(line_data[0], "%Y/%m/%d %H:%M:%S.%f").timestamp(),
                'latitude': line_data[1],
                'longitude': line_data[2],
                'height': line_data[3],
                'Q': line_data[4],
                'ns': line_data[5],
                'sdn': line_data[6],
                'sde': line_data[7],
            })
    return pos


def generate_geo_json(timestamp_file_name, pos_list):
    print(timestamp_file_name)
    timestamp_json = read_json_file(timestamp_file_name)
    positions = iter(pos_list)
    timestamps = timestamp_json['timestamps']
    features = []
    pos = next(positions)
    previous_pos = pos
    try:
        for timestamp in timestamps:
            while not previous_pos['GPST'] < timestamp[1]/1000000000 <= pos['GPST']:
                previous_pos = pos
                pos = next(positions)

            prop = {
                "index": timestamp[0],
                "timestamp": timestamp[1]
            }
            features.append(
                geojson.Feature(
                    geometry=geojson.Point((float(previous_pos['latitude']), float(previous_pos['longitude']))),
                    properties=prop
                )
            )
    except StopIteration:
        pass
    feature_collection = geojson.FeatureCollection(
        features, filename=timestamp_json["filename"], device_alias=timestamp_json["device_alias"],
        total=len(timestamp_json['timestamps']), beginning=timestamp_json['timestamps'][0][1],
        end=timestamp_json['timestamps'][-1][1]
    )
    return feature_collection


def generate_geojson(path_to_files):
    try:
        lsprocess = subprocess.check_output("ls %s" % path_to_files, shell=True)
        lsprocess = lsprocess.decode("utf-8")
    except subprocess.CalledProcessError:
        print("Wrong path")
        return
    files = lsprocess.split('\n')
    json_files = []
    gps_file = None
    for file in files:
        if file.endswith('.json'):
            json_files.append(os.path.join(path_to_files, file))
        elif file.endswith('.pos'):
            gps_file = os.path.join(path_to_files, file)
    pos_list = read_pos_file(gps_file)
    geojson_list = []
    for json_file in json_files:
        geojson_list.append(generate_geo_json(json_file, pos_list))
    return  geojson_list


def main():
    print(generate_geojson('example'))


if __name__ == "__main__":
    main()
