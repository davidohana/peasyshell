# peasyshell

Python easy shell utilities. Stop writing bash scripts and use Python instead.

Compatible with Python 2.7 and Python 3.5+.  
Tested on Mac and Ubuntu.

The story [behind it](https://davidoha.medium.com/avoiding-bash-frustration-use-python-for-shell-scripts-44bba8ba1e9e?source=friends_link&sk=a92de79cb005aa919eadaae811e3acbb).

```python
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
```

Output: 

![](docs/sample_app_docker_output.png)

Another example [here](sample_app.py).

### How to use 

Copy [peasyshell.py](peasyshell.py) next to your Python shell script and import it. 

### License: 
Apache-2.0

