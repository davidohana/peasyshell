#!/usr/bin/env python2

from peasyshell import *

# initialize logging to stdout in colors by severity level
init_logging()

cfg = {
    "container_name": "ES",
    "image_name": "elasticsearch:6.8.13"
}

get_latest = yes_or_no("get latest version?")
if get_latest:
    sh("docker image pull {image_name}", **cfg)

container_id = sh("docker ps -q -a -f name=^/{container_name}$", capture_out=True, **cfg).stdout
if container_id:
    logger.info("removing old container with ID " + container_id)
    sh("docker rm -f {}", container_id)
else:
    logger.info("container does not exist")

container_id = sh("docker run -d --name {container_name} {image_name}", capture_out=True, **cfg).stdout

sh("docker logs {} -f", container_id, timeout_sec=5)

logger.info("done")
