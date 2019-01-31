# iDAQdl-CLI
A Python CLI for downloading log files from the Wamore iDAQ

```
Available Log Files:
1. LOG.001    0.49 MB   2019-01-31 01:55:04
2. LOG.002    0.41 MB   2019-01-31 01:56:46
3. LOG.003    3.15 MB   2019-01-31 02:27:30

Select log file(s) to download
Request multiple files with a comma separated list (e.g. 2, 3, 4)
?: 3
Enter save path
? [.]: 

Enter file name for LOG.003
.iDAQ will be appended automatically
? [LOG.003]: my_log_file
LOG.003:  62%|██████████▋     | 2.06M/3.30M [00:03<00:02, 578kb/s
```

## Installation
iDAQdl-CLI uses [Poetry](https://github.com/sdispater/poetry) for installation and dependency management

With Poetry installed, iDAQdl-CLI can be installed with the following one-liner in your cloned project repository:

```
$ poetry install
```

If you do not want to install the development dependencies, you can install with the following:

```
$ poetry install --no-dev
```

Poetry utilizes virtual environments to isolate project packages from the user's main Python installation. For users unfamiliar with virtual environments, Poetry provides easy activation with its `shell` command:

```
$ poetry shell
```

All commands in the remainder of this README assume an activated virtual environment.

## Usage
This package assumes the user's ethernet adapter is configured with a static IP of: `192.168.1.1` and the iDAQ is configured with a static IP of `192.168.1.2`.

A guided CLI can be accessed by invoking `iDAQcli.py` without any arguments:

```
$ python iDAQcli.py
```

### Command Line Arguments
CLI prompts may be bypassed by providing arguments on invocation

#### `--dlall`, `-a`
Download all log files present on the iDAQ.

This argument is a flag.

```
$ python iDAQcli.py --dlall

Available Log Files:
1. LOG.001    0.49 MB   2019-01-31 01:55:04
2. LOG.002    0.41 MB   2019-01-31 01:56:46
3. LOG.003    3.15 MB   2019-01-31 02:27:30

Downloading all log files
Enter save path
? [.]: 
```

#### `--dlpath`, `-p`
Specify a download directory, *str*

```
$ python iDAQcli.py --dlpath ./logs

Available Log Files:
1. LOG.001    0.49 MB   2019-01-31 01:55:04
2. LOG.002    0.41 MB   2019-01-31 01:56:46
3. LOG.003    3.15 MB   2019-01-31 02:27:30

Select log file(s) to download
Request multiple files with a comma separated list (e.g. 2, 3, 4)
?: 3

Enter file name for LOG.003
.iDAQ will be appended automatically
? [LOG.003]: 
```

## Developing
iDAQdl-CLI uses [flake8](https://github.com/PyCQA/flake8) (with extensions) and [black](https://github.com/ambv/black) to enforce code style. All packages and configuration files are included as development dependencies for this project.

A [pre-commit](https://github.com/pre-commit/pre-commit) configuration is also included with this project to set up precommit git hooks for linting and code formatting enforcement. `pre-commit` is also included as a development dependency for this project.