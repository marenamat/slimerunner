#!/usr/bin/python3

import json
import requests
import time
import zlib
#from .Config import Config as C

class Encoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, default=self.excls)

    def excls(self, obj):
        if isinstance(obj, Encodable):
            return { **{
                    k: v for k,v in obj.__dict__.items()
                    if not k.startswith("__")
                    }, **obj.data }


class Job:
    def __init__(self, *, runner, id, token, job_info, git_info, runner_info, variables, artifacts, dependencies, **kwargs):
        self.runner = runner
        self.id = id
        self.token = token
        self.job_info = job_info
        self.git_info = git_info
        self.runner_info = runner_info
        self.variables = variables
        self.env = { x["key"]: x["value"] for x in variables }
        self.artifacts = artifacts
        self.dependencies = dependencies

        self.kwargs = kwargs
        self._log = []
        self._loglen = 0

    def update_state(self, state, **kwargs):
        JobState(self, state, **kwargs).exchange()

    def log(self, msg):
        print(msg)

        msg = (msg + "\n").encode()
        ol = self._loglen
        self._loglen += (ml := len(msg))

        c = self.runner.config
        r = requests.request(
                method="PATCH", 
                url=c.url + "/api/v4/" + f"jobs/{self.id}/trace?debug_trace=false",
                headers={
                    "Content-Type": "text/plain",
                    "Runner-Token": c.token,
                    "Job-Token": self.token,
                    "Content-Range": f"{ol}-{self._loglen}"
                    },
                data=msg,
                )
#        print(r.status_code)

        self._log.append(msg)

    def __enter__(self):
        self.update_state("running")
        return self

    def __exit__(self, et, *args):
        if et:
            self.update_state("failed")
        else:
            fulllog = b"".join(self._log)
            crc = zlib.crc32(fulllog)

            self.update_state(
                    state="success",
                    checksum=f"crc32:{crc:08x}",
                    output={
                        "checksum": f"crc32:{crc:08x}",
                        "bytesize": self._loglen,
                        },
                    )

class Runner:
    def cmd(self, cls):
        def foo(**data):
            o = cls(runner=self, **data)
            return o.finish(o.exchange())
        return foo

    def __init__(self, config):
        self.config = config
        self.encoder = Encoder()
        self.verify = self.cmd(Verify)
        self.request_job = self.cmd(RequestJob)

    def wait_for_job(self):
        while not (j := self.request_job()):
            time.sleep(10)

        return j

    def jobs(self):
        while j := self.wait_for_job():
            with Job(runner=self, **j) as jj:
                yield jj


class Encodable:
    def __init__(self, runner, **data):
        self.runner = runner
        self.data = data

class Exchange(Encodable):
    _method = "POST"
    _headers = {}

    def __init__(self, **data):
        super().__init__(**data)

        c = self.runner.config
        self.token = c.token
        self.system_id = c.system_id

    def exchange(self):
        c = self.runner.config

#        print("send request: ", {
#              "method": self._method,
#              "url": c.url + "/api/v4/" + self._url,
#              "headers": {
#                    "Content-Type": "application/json",
#                    "Runner-Token": c.token,
#                    "Accept": "application/json",
#                    **self._headers,
#                    },
#              "data": self.runner.encoder.encode(self),
#              })


        r = requests.request(
                method=self._method,
                url=c.url + "/api/v4/" + self._url,
                headers={
                    "Content-Type": "application/json",
                    "Runner-Token": c.token,
                    "Accept": "application/json",
                    **self._headers,
                    },
                data=self.runner.encoder.encode(self),
                )

        r.raise_for_status()
        if r.status_code == 204:
            return False

#        print(r.status_code)
#        print(r.content)
        return r.json()

    def finish(self, r):
        return r

class Verify(Exchange):
    _url = "runners/verify"

class RunnerFeatures(Encodable):
    def __init__(self, **data):
        super().__init__(**data)
        self.artifacts = True
        self.upload_multiple_artifacts = True
        self.upload_raw_artifacts = True
        self.cancelable = False

class RunnerInfo(Encodable):
    def __init__(self, **data):
        super().__init__(**data)

        r = self.runner

        self.name = r.name
        self.version = r.version
        self.revision = r.revision
        self.platform = r.platform
        self.architecture = r.architecture
        self.executor = "custom"
        self.features = RunnerFeatures(runner=self.runner)

class RequestJob(Exchange):
    _url = "jobs/request"

    def __init__(self, **data):
        super().__init__(**data)

        self.info = RunnerInfo(runner=self.runner)
        self.config = Encodable(runner=self.runner)

class JobState(Exchange):
    _method = "PUT"

    def __init__(self, job, state, **data):
        super().__init__(runner=job.runner, **data)

        self.info = RunnerInfo(runner=self.runner)
        self.state = state
        self._url = "jobs/" + str(job.id)
        self._headers["Job-Token"] = job.token
        self.token = job.token
