from Runner import Runner
from Config import Config

### The Config class should look like this:
# class Config:
#    system_id = "s_abcdef123456"
#    token = "glrt-..." (received by registering the runner)
#    url = "https://..." (the base URI, without /api/v4)

import pathlib
import time

class TestRunner(Runner):
    name = "meowee"
    version = "0.0.0"
    revision = "nya"
    platform = "linux"
    architecture = "amd64"

r = TestRunner(Config)
print(r.verify())

for j in r.jobs():
    j.download_artifacts("wrooo")
    for q in range(4):
        j.log(f"meow {q}")
#        j.checkin_artifact(f"meow {q}", apath=f"meow{q}.txt")
        with open(f"wrooo/nya{q}.txt", "a") as n:
            n.write("meow")
#            j.checkin_artifact(pathlib.Path(f"wrooo/nya{q}.txt"), apath=f"nya/wrooo{q}.txt")
#            j.checkin_artifact(f"nya {q}", apath=f"a/b/{q}/d/e/f.txt")

        time.sleep(1)

    j.checkin_artifact("SAMALAMADINGDONG", apath="changegamer")
