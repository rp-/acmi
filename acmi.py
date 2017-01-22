import os
import zipfile
import codecs
import datetime


class Object:
    def __init__(self, id):
        self.id = id
        self.type = None
        self.parent = None
        self.name = None
        self.pilot = None
        self.group = None
        self.country = None


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

    def load(self, filepath):

        def acmifile(filepath_):
            if zipfile.is_zipfile(filepath_):
                with zipfile.ZipFile(filepath_) as acmizip:
                    return acmizip.open(os.path.basename(filepath_).replace("zip", "txt"), mode="rU")
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

    def _parse_object(self, obj: Object, fields):
        for field in fields[1:]:
            (prop, val) = field.split('=', 1)
            if prop == "Name":
                obj.name = val
            elif prop == "Type":
                obj.type = val
            elif prop == "Country":
                obj.country = val

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
            else:
                raise RuntimeError("ACMI file missing FileVersion.")

            cur_reftime = None
            for rawline in codecs.iterdecode(f, Acmi._codec):
                line = rawline.strip()
                if line.startswith('//'):
                    continue  # ignore comments

                if line.startswith('#'):
                    cur_reftime = float(line[1:])
                    continue

                if line.startswith('-'):
                    pass  # remove object
                else:
                    fields = self.split_fields(line)
                    obj_id = int(fields[0], 16)

                    if obj_id == 0:
                        self._parse_global_property(fields)
                    else:
                        if obj_id not in self.objects:
                            obj = Object(obj_id)
                            self.objects[obj_id] = obj
                            self._parse_object(obj, fields)
                    print(obj_id, fields)

            print("cur_reftime", cur_reftime)

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
    acmi.load("C:\\Users\\peint\\Documents\\Tacview\\Tacview-20170120-175227-DCS-dcscs.zip.acmi")

    for oid in acmi.objects:
        o = acmi.objects[oid]
        print(o.id, o.name)

    print(acmi)
