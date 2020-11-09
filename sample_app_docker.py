#!/usr/bin/env python2

from peasyshell import *

# initialize logging to stdout in colors by severity level
init_logging()

cfg = {
    "container_name": "ELASTIC",
    "image_name": "elasticsearch:6.8.13"
}

get_latest = yes_or_no("get latest version?")
if get_latest:
    # run a formatted command, output is send to stdout, terminate on cmd failure
    sh("docker image pull {image_name}", **cfg)

# run a formatted command and capture standard output stream, do not terminate on error. Shell enabled to allow piping.
res = sh("docker ps -a | grep {container_name}", shell=True, capture_out=True, exit_on_fail=False, **cfg)
# grep error code 0 means search string found
if res.returncode == 0:
    # process the output conveniently, no need for awk/sed
    old_container_id = res.stdout.split()[0]
    logger.info("removing old container with ID " + old_container_id)
    # cmd formatting is also possible with positional arguments
    sh("docker rm -f {}", [old_container_id])
else:
    logger.info("container does not exist")

sh("docker run -d --name {container_name} {image_name}", capture_out=True, **cfg)

# run command and stop if after 5 seconds
# last result always stored in shres local variable
sh("docker logs {} -f", [shres.stdout], timeout_sec=5)

logger.info("done")
