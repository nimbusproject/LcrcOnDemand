#!/usr/bin/env python

import spur
import subprocess
import threading
import argparse
import re
import os
import time
import shutil

# global variables
lcrc_host_ips = []

WORKERS_PER_HOST = 24
LCRC_WORKERS = 372

def ClearCachedKey():
    print "Clear cached host keys ..."

    for _ip in lcrc_host_ips:
        cmd = "ssh-keygen -R %s" % _ip
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        cmd = "ssh-keyscan %s >> ~/.ssh/known_hosts" % _ip
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)


def InstallDockerThread(host_ip):
    shell = spur.SshShell(hostname=host_ip, username="cc", missing_host_key=spur.ssh.MissingHostKey.accept)

    with shell.open("/home/cc/install_docker.sh", "wb") as remote_file:
        with open("./install_docker.sh", "rb") as local_file:
            shutil.copyfileobj(local_file, remote_file)

    with shell:
        shell.run(["sh", "-c", "chmod u+x ./install_docker.sh && ./install_docker.sh"], allow_error=False)


def JoinSwarmThread(host_ip, token, leader_ip):
    shell = spur.SshShell(hostname=host_ip, username="cc", missing_host_key=spur.ssh.MissingHostKey.accept)

    with shell:
        shell.run(["sh", "-c", "docker swarm join --token {} {}:2377".format(token, leader_ip)], allow_error=False)


def RunOnAllHosts(target_func, arguments=[]):

    _threads = []
    for _ip in lcrc_host_ips:
        _t = threading.Thread(target=target_func, args=[_ip]+arguments)
        _t.start()
        _threads.append(_t)

    for _t in _threads:
        _t.join()


def LaunchAllWorkers(launch_missing):
    num_workers = 0

    for host_id, host_ip in enumerate(lcrc_host_ips):
        shell = spur.SshShell(hostname=host_ip, username="cc", missing_host_key=spur.ssh.MissingHostKey.accept)
        with shell:
            result = shell.run(["sh", "-c", "docker pull jtqv84/openstack_torque_worker"], allow_error=False)
	for i in range(1, WORKERS_PER_HOST + 1):
            if launch_missing:
                cmd = 'docker inspect lcrc-worker-{}'.format(num_workers + 1)
                shell = spur.SshShell(hostname=host_ip, username="cc", missing_host_key=spur.ssh.MissingHostKey.accept)
                with shell:
                    result = shell.run(["sh", "-c", cmd], allow_error=True)
	            if result.return_code != 0:
                        print 'lcrc-worker-{} is missing'.format(num_workers + 1)
                    else:
                        num_workers += 1
	                if num_workers >= LCRC_WORKERS:
                            return
                        continue

            cmd = 'docker run -itd'
            if not launch_missing:
                cmd += ' -e "WAIT_CONTROLLER=true"'
            cmd += ' --rm --privileged'
            cmd += ' --name lcrc-worker-{}'.format(num_workers + 1)
            cmd += ' --hostname lcrc-worker-{}'.format(num_workers + 1)
            cmd += ' --network hpc-cluster-network'
            cmd += ' -v /lib/modules:/lib/modules'
            cmd += ' jtqv84/openstack_torque_worker'
	    print "Run lcrc-worker-{} on lcrc-host-{}: {}".format(num_workers + 1, host_id + 1, cmd)

            shell = spur.SshShell(hostname=host_ip, username="cc", missing_host_key=spur.ssh.MissingHostKey.accept)
            with shell:
                result = shell.run(["sh", "-c", cmd], allow_error=False)
                print result.output
	        if result.return_code != 0:
                    print result.stderr_output

            num_workers += 1
	    if num_workers >= LCRC_WORKERS:
                return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch-missing", action="store_true", help="Launch missing lcrc-workers")
    parser.add_argument("-r", "--nova-repo", default="https://github.com/Francis-Liu/animated-broccoli.git", help="NOVA_REPO, git repository of private NOVA code")
    parser.add_argument("-n", "--nova-branch", default="support-W", help="NOVA_BRANCH, branch in the git repository of private NOVA code")
    parser.add_argument("lcrc_workers", help="number of lcrc-worker nodes", type=int)
    parser.add_argument("-H", "--pssh-hosts", default="/home/cc/pssh_hosts.txt", help="absolute path of the pssh hosts file")
    args = parser.parse_args()
    global LCRC_WORKERS, lcrc_host_ips
    LCRC_WORKERS = args.lcrc_workers
    with open(args.pssh_hosts) as f:
        lcrc_host_ips = [_i.strip() for _i in f.readlines()]

    ClearCachedKey()

    # print "Install Docker on all lcrc-host nodes ..."
    # RunOnAllHosts(InstallDockerThread)

    # print "Join Docker Swarm on all lcrc-host nodes ..."
    # RunOnAllHosts(JoinSwarmThread, ['SWMTKN-1-07ix7sid6jxmtt15pmyz3vmqbcjk4zlg1bgupchmvjyoipakks-1518fpkeka5xtcu32zb5qthn4', '10.40.1.137'])

    # docker run -it -e "LCRC_WORKERS=372" --rm --privileged --name lcrc-head --hostname lcrc-head --network hpc-cluster-network -v /lib/modules:/lib/modules jtqv84/openstack_torque_master

    LaunchAllWorkers(args.launch_missing)

if __name__ == "__main__":
    main()
