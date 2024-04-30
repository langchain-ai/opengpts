#!/usr/bin/env python

import click
import pathlib
import docker
import tempfile
import string
import shutil
import time

# We need to install a set of relevant packages so that our users can use
# the python we've installed for them. If we were working with traditional
# python environments, we might require our users to specify a
# `requirements.txt` file to enumerate their dependencies. This is robust from
# an infra perspective, but most likely places too high a burden on Python code
# generators at the moment. Controlling our python environment also has
# security benefits, but requires us to manually add new capabilities if our
# users supply Python sources with libraries we have not installed on our
# testbed.
DOCKERFILE_TEMPLATE = """
FROM $base_image

# Setup working directory
RUN mkdir -p $workdir
WORKDIR $workdir
RUN chown $user:$group $workdir

# Copy workload into place
ADD $workload $workdir/$workload

# Install python
RUN apk add python3

# Set user identity
USER $user:$group

# Run workload
CMD python $workdir/$workload
"""


@click.command()
@click.argument("workload", metavar="<workload.py>", type=click.Path(exists=True))
def eval_tool(workload: pathlib.Path):
    workload = pathlib.Path(workload).absolute()
    if not workload.is_file():
        raise click.UsageError(f"Filename {workload} does is not a regular file.")
    if workload.suffix != ".py":
        raise click.UsageError(f"Filename {workload} is not a python file.")
    client = docker.from_env()

    # In order to add our workload file to the image, we need to provide the
    # relative path from the Dockerfile context to the workload file, and the
    # file must be in a subtree of the Dockerfile context dir. The Docker SDK
    # provides the ability to pass a fileobj directly, however, it generates a
    # tempfile location for the Dockerfile context, and so we cannot place our
    # target file inside of the context. Therefore, we generate a tempfile of
    # our own, and assemble the image that way.
    click.echo(f"Building image for {workload}")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = pathlib.Path(tmp_dir)
        shutil.copy(workload, tmp_dir_path.joinpath("workload.py"))
        with open(tmp_dir_path.joinpath("Dockerfile"), mode="wb") as df:
            df.write(
                string.Template(DOCKERFILE_TEMPLATE)
                .substitute(
                    base_image="alpine",
                    workdir="/workdir",
                    workload="workload.py",
                    user="nobody",
                    group="nobody",
                )
                .encode()
            )
        image, _ = client.images.build(path=tmp_dir, rm=True)
    click.echo(f"Image: {image.id}")

    container_opts = {
        # Clean up container on exit
        "remove": True,
        # Create unique cgroup for this container
        "cgroupns": "private",
        # Do not consume too many resources
        "mem_limit": "4gb",
        # Do not give extended privileges to the container
        "privileged": False,
        "security_opt": ["no-new-privileges=true"],
        # Mount root filesystem as readonly
        "read_only": True,
    }
    click.echo("Running container")
    start = time.time()
    output = client.containers.run(image, **container_opts)
    end = time.time()
    click.echo("Done")
    click.echo("========")
    click.echo(output)
    click.echo("========")
    click.echo(f"({end-start})")


if __name__ == "__main__":
    eval_tool()
