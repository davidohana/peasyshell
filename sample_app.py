#!/usr/bin/env python2

from peasyshell import *

init_logging()

sh("ls -al", log_process_id=True)

sh("ping 127.0.0.1", timeout_sec=3, echo_cmd=False, echo_cmd_args=True)

sh("""cat peasyshell.py 
        | grep import""", shell=True, shell_single_command=True)

hostname = sh("hostname -f", capture_out=True, output_remove_trailing_newlines=True).stdout
print("my hostname is [{}]".format(hostname))

hostname = sh("hostname -f", capture_out=True, output_remove_trailing_newlines=False).stdout
print("my hostname is [{}]".format(hostname))

os.environ["my_var1"] = "foo"
sh("echo **$my_var1**", shell=True)

sh("echo **$my_var2**", shell=True, env={"my_var2": "bar"})

out = sh("ps aux | grep sample_app | grep -v grep", shell=True, capture_out=True).stdout
pid = out.split()[1]
print("my process ID: " + pid)

exit_on_fail = yes_or_no("exit on fail?")
# next command will fail because -X arg does not exist
# and as a result the python script will terminate
sh("hostname -X", exit_on_fail=exit_on_fail, log_process_id=True)

print ("bye")
