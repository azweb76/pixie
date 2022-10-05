# Pixie SDK

Python-based tool used to run pixie scripts. Pixie scripts are YAML files that contain one or more jobs with parameters and steps.

```yaml
# in .pixie.yaml
name: pixie1

jobs:
    hello:
        parameters:
        - name: Name
        steps:
        - print: Hello ${{ Name }}!
```

```bash
# run hello job from the same directory as the .pixie.yaml file
$ pixie run hello
[?] Name: Dan
Hello Dan!

$ pixie run hello -c Name=John
Hello John!
```

## Install

```shell
# install pixie
pipx install git+https://github.com/azweb76/pixie

# update pixie
pipx upgrade pixie-sdk
```

## Usage

|command|description|
|---|---|
|`discover`|Discover pixies in a package.|
|`info`|Show information for a job.|
|`run`|Used to run a pixie job.|

### discover

```text
Usage: pixie discover [OPTIONS] [PACKAGE]

  Discover pixies in a package.

Options:
  -s, --save  Path to the pixie script.
  -h, --help  Show this message and exit.
```

### info

```text
Usage: pixie info [OPTIONS] JOB

  Show information for a job.

Options:
  -p, --package TEXT  Pixie package name.
  -s, --script PATH   Path to the pixie script.
  -h, --help          Show this message and exit.
```

### run

```text
Usage: pixie run [OPTIONS] JOB

  Used to run a pixie job.

Options:
  -p, --package TEXT   Package to run.
  -s, --script PATH    Path to the pixie script.
  -c, --context TEXT   Context values to set.
  --context-from PATH  File used to set context
  -t, --target PATH    Directory to use when generating files
  -h, --help           Show this message and exit.
```
