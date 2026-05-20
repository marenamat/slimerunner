from Runner import Runner
from Config import Config

### The Config class should look like this:
# class Config:
#    system_id = "s_abcdef123456"
#    token = "glrt-..." (received by registering the runner)
#    url = "https://..." (the base URI, without /api/v4)

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
    for q in range(10):
        j.log(f"meow {q}")
        time.sleep(1)
