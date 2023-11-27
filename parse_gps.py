from argparse import ArgumentParser
import xml.etree.ElementTree as ET
import json

# Coordinates of the area of interest, Ouluzone
MIN_LAT=65.175401
MAX_LAT=65.183293
MIN_LON=26.030708
MAX_LON=26.058937


def parse_args():
    parser = ArgumentParser(description='Parse gpx file')
    parser.add_argument('xmlfile', help='gpx file')
    return parser.parse_args()


def main():
    args = parse_args()
    with open("points.json", "w") as f:
        json.dump(parse_gpx(args.xmlfile), f, indent=2)


def parse_gpx(xmlfile):
    ns_map = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    points = {}

    for _, elem in ET.iterparse(xmlfile, events=('end',)):
        if elem.tag == f"{{{ns_map['gpx']}}}trkpt":
            lat = float(elem.attrib.get("lat", 0))
            lon = float(elem.attrib.get("lon", 0))
            if MIN_LAT < lat < MAX_LAT and MIN_LON < lon < MAX_LON:
                time_elem = elem.find(f"{{{ns_map['gpx']}}}time")
                if time_elem is not None:
                    points[time_elem.text] = {"lat": lat, "lon": lon}
            elem.clear()

    return points


if __name__ == "__main__":
    main()
