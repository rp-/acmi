import sys
import os
import zipfile
import codecs
import datetime
import sortedcontainers


class Object:
    def __init__(self, id):
        self.id = id
        self.removed_at = None

        self.data = {}

    def set_value(self, field, timeframe, val):
        if field not in self.data:
            self.data[field] = sortedcontainers.SortedDict()
        self.data[field][timeframe] = val

    def value(self, field: str, time=None):
        if field not in self.data:
            return None

        if time is not None:
            return self.data[field].bisect_left(time)
        return self.data[field][self.data[field].keys()[-1]]

    def group(self, time=None):
        return self.value("Group", time)

    def __str__(self):
        return "{id}: '{name}' {long}, {lat}, {alt}".format(
            id=self.id,
            name=self.value("Name"),
            long=self.value("Longitude"),
            lat=self.value("Latitude"),
            alt=self.value("Altitude"))


class Frame:
    def __init__(self, time):
        self.time = time
        self.objects = {}


class Acmi:
    _codec = 'utf-8-sig'

    def __init__(self):
        self.file_version = None
        self.file_type = None

        # global properties
        self.data_source = None
        self.data_recorder = None
        self.reference_time = None
        self.recording_time = None
        self.author = None
        self.title = None
        self.category = None
        self.briefing = None
        self.debriefing = None
        self.comments = None
        self.reference_longitude = None
        self.reference_latitude = None

        self.objects = {}
        self.timeframes = []

    def load(self, filepath):

        def acmifile(filepath_):
            if zipfile.is_zipfile(filepath_):
                with zipfile.ZipFile(filepath_) as acmizip:
                    return acmizip.open(os.path.basename(filepath_).replace("zip", "txt"), mode="r")
            return open(filepath_)

        self._parse(acmifile(filepath))

    @staticmethod
    def split_fields(line):
        return line.split(',')

    def _parse_global_property(self, fields):
        for field in fields[1:]:  # skip objid (0)
            (prop, val) = field.split('=', 1)
            if prop == "ReferenceTime":
                self.reference_time = datetime.datetime.strptime(val, "%Y-%m-%dT%H:%M:%SZ")
            elif prop == "RecordingTime":
                self.recording_time = datetime.datetime.strptime(val, "%Y-%m-%dT%H:%M:%SZ")
            elif prop == "ReferenceLongitude":
                self.reference_longitude = float(val)
            elif prop == "ReferenceLatitude":
                self.reference_latitude = float(val)
            elif prop == "DataSource":
                self.data_source = val
            elif prop == "DataRecorder":
                self.data_recorder = val
            elif prop == "Author":
                self.author = val
            elif prop == "Title":
                self.title = val
            elif prop == "Category":
                self.category = val
            elif prop == "Briefing":
                self.briefing = val
            elif prop == "Debriefing":
                self.debriefing = val
            elif prop == "Comments":
                self.comments = val
            else:
                raise RuntimeError("Unknown global property: " + prop)

    def _update_object(self, obj_id: int, timeframe: float, fields):
        if obj_id not in self.objects:
            self.objects[obj_id] = Object(obj_id)

        obj = self.objects[obj_id]
        for field in fields[1:]:
            (prop, val) = field.split('=', 1)
            if prop == "T":
                pos = val.split('|')
                if pos:
                    if pos[0]:
                        obj.set_value("Longitude", timeframe, float(pos[0]))
                    if pos[1]:
                        obj.set_value("Latitude", timeframe, float(pos[1]))
                    if pos[2]:
                        obj.set_value("Altitude", timeframe, float(pos[2]))
            elif prop == "Name":
                obj.set_value(prop, timeframe, val)
            elif prop == "Parent" or prop == "FocusTarget" or prop == "LockedTarget":
                obj.set_value(prop, timeframe, int(val, 16))
            elif prop in ["Type", "Pilot", "Group", "Country", "Coalition",
                          "Color", "Registration", "Squawk", "Debug", "Label"]:
                obj.set_value(prop, timeframe, val)
            # numeric except coordinates start here
            # floats
            elif prop == ["Importance", "Length", "Width", "Height",
                          "IAS", "CAS", "TAS", "Mach", "AOA", "HDG"
                          "HDM", "Throttle", "RadarAzimuth", "RadarElevation",
                          "RadarRange", "LockedTargetAzimuth",
                          "LockedTargetElevation", "LockedTargetRange"]:
                obj.set_value(prop, timeframe, float(val))
            # int
            elif prop == ["Slot", "Afterburner", "AirBrakes", "Tailhook"
                          "Parachute", "DragChute", "RadarMode",
                          "LockedTargetMode"]:
                obj.set_value(prop, timeframe, int(val))
            else:
                print("Unknown property:", prop)

    def _parse(self, fp):
        with fp as f:
            rawline = f.readline().decode(Acmi._codec)
            if rawline.startswith('FileType='):
                self.file_type = rawline[len('FileType='):].strip()
            else:
                raise RuntimeError("ACMI file doesn't start with FileType.")

            rawline = f.readline().decode(Acmi._codec)
            if rawline.startswith('FileVersion='):
                self.file_version = float(rawline[len('FileVersion='):].strip())
                if self.file_version < 2.1:
                    raise RuntimeError("Unsupported file version: {v}".format(v=self.file_version))
            else:
                raise RuntimeError("ACMI file missing FileVersion.")

            cur_reftime = 0.0
            for rawline in codecs.iterdecode(f, Acmi._codec):
                line = rawline.strip()
                if line.startswith('//'):
                    continue  # ignore comments

                if line.startswith('#'):
                    cur_reftime = float(line[1:])
                    self.timeframes.append(cur_reftime)
                    continue

                if line.startswith('-'):
                    obj_id = int(line[1:], 16)
                    self.objects[obj_id].removed_at = cur_reftime
                else:
                    fields = self.split_fields(line)
                    obj_id = int(fields[0], 16)

                    #print(obj_id, fields)
                    if obj_id == 0:
                        self._parse_global_property(fields)
                    else:
                        self._update_object(obj_id, cur_reftime, fields)

    def object_ids(self):
        return self.objects.keys()

    def __str__(self):
        return str(
            {
                "FileType": self.file_type,
                "FileVersion": self.file_version,
                "DataSource": self.data_source,
                "DataRecorder": self.data_recorder,
                "ReferenceTime": self.reference_time.isoformat(),
                "RecordingTime": self.recording_time.isoformat(),
                "Author": self.author,
                "Title": self.title,
                "Category": self.category,
                "Briefing": self.briefing,
                "Debriefing": self.debriefing,
                "Comments": self.comments,
                "ReferenceLongitude": self.reference_longitude,
                "ReferenceLatitude": self.reference_latitude
            }
        )


if __name__ == "__main__":
    acmi = Acmi()
    #acmi.load("C:\\Users\\peint\\Documents\\Tacview\\Tacview-20170120-175227-DCS-dcscs.zip.acmi")
    acmi.load(sys.argv[1])

    print(acmi.object_ids())
    print(acmi.timeframes)
    for oid in acmi.objects:
        o = acmi.objects[oid]
        if o.removed_at is None:
            print(o)

    print(acmi)
