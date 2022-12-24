#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Arash Keshavarzi <arash@ca-studios.com=>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# from tabnanny import verbose
# from typing_extensions import ParamSpec

DOCUMENTATION = r'''
---
module: gitlab_download
short_description: Downloading artifact/archives from gitlab
version_added: "1.0.0"
description: 
    - Download artifact or repository archives from gitlab.
author:
    - Arash Keshavarzi (@arash-ke)
requirements:
    - python-gitlab >= 3.12.0
    - python-slugify >= 4.0.1
options:
  server_url:
    description:
      - Gitlab server base url
    type: str
    required: true
  project_id:
    description:
      - Id of project that we wan't to download from
    type: str
    required: true
  force:
    description:
      - Force download if file already exists.
      - If there is mismatch in refrences or pipeline.
    type: bool
    default: false
  type:
    description:
      - C(artifact) Download an artifact from job.
      - C(release) Download a release file.
      - C(archive) Download a repository archive.
    type: str
    choices:
    - artifact
    - release
    - archive
    required: true
  state:
    description:
      - To be filled.
    type: str
    choices:
    - download
    - query
    default: download
  ref:
    description:
      - To be filled.
    type: str
    default: ''
  commit:
    description:
      - To be filled.
    type: str
  dest:
    description:
      - To be filled.
    type: str
    required: true
  filename:
    description:
      - To be filled.
    type: str
  filename_prefix:
    description:
      - To be filled.
    type: str
  filename_postfix:
    description:
      - To be filled.
    type: str
  commit_as_filename:
    description:
      - To be filled.
    type: bool
    default: false
  project_as_filename:
    description:
      - To be filled.
    type: bool
    default: false
  append_commit:
    description:
      - To be filled.
    type: bool
    default: false
  append_project:
    description:
      - To be filled.
    type: bool
    default: false
  append_ref:
    description:
      - To be filled.
    type: bool
    default: false
  only_info:
    description:
      - To be filled.
    type: bool
    default: false
  artifact:
    description:
        - To be filled.
    type: dict
    options:
      job_name:
        description:
            - To be filled.
        type: str
        required: true
      job:
        description:
            - To be filled.
        type: str
      pipeline:
        description:
            - To be filled.
        type: str
      check_pipeline_status:
        description:
            - To be filled.
        type: bool
        default: true
      pipeline_status:
        description:
            - To be filled.
        type: str
        choices:
            - success
            - running
        default: success
      allow_running_pipeline:
        description:
            - To be filled.
        type: bool
        default: false
  archive:
    description:
        - To be filled.
    type: dict
    options:
      format:
        description:
            - To be filled.
        type: str
        default: tar.gz
  connection_options:
    description:
        - To be filled.
    type: dict
    default: {}
    options:
      private_token:
        description:
            - To be filled.
        type: str
        no_log: true
      oauth_token:
        description:
            - To be filled.
        type: str
      job_token:
        description:
            - To be filled.
        type: str
      ssl_verify:
        description:
            - To be filled.
        type: bool
      timeout:
        description:
            - To be filled.
        type: float
      http_username:
        description:
            - To be filled.
        type: str
      http_password:
        description:
            - To be filled.
        type: str
      pagination:
        description:
            - To be filled.
        type: str
      order_by:
        description:
            - To be filled.
        type: str
      user_agent:
        description:
            - To be filled.
        type: str
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

# from matplotlib.font_manager import json_dump

import gitlab
import json
import os
import shutil
import tempfile
# import traceback
from slugify import slugify

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native, to_text

module = AnsibleModule(
    supports_check_mode=True,
    # add_file_common_args=True,
    argument_spec = dict(
        server_url = dict(type="str", required=True),
        project_id = dict(type="str", required=True),
        force = dict(type="bool", default=False),
        type = dict(type='str', choices=list(['artifact', 'release', 'archive']), required=True),
        state = dict(type='str', choices=list(['download', 'query']), default='download'),
        ref = dict(type="str", default=''),
        commit = dict(type="str"),
        dest = dict(type="str", required=True),
        filename = dict(type="str"),
        filename_prefix = dict(type="str"),
        filename_postfix = dict(type="str"),
        commit_as_filename = dict(type='bool', default=False),
        project_as_filename = dict(type='bool', default=False),
        append_commit = dict(type='bool', default=False),
        append_project = dict(type='bool', default=False),
        append_ref = dict(type='bool', default=False),
        only_info = dict(type="bool", default=False),
        artifact = dict(
            type="dict",
            options = dict(
                job_name = dict(type='str', required=True),
                job = dict(type='str'),
                pipeline = dict(type='str'),
                check_pipeline_status = dict(type="bool", default=True),
                pipeline_status = dict(type="str", choices=list(['success', 'running']), default='success'),
                allow_running_pipeline = dict(type="bool", default=False),
            ),
        ),
        archive = dict(
            type="dict",
            options = dict(
                format = dict(type="str", default='tar.gz'),
            ),
        ),
        connection_options = dict(
            type="dict",
            default = dict(),
            options = dict(
                private_token = dict(type='str', no_log=True),
                oauth_token = dict(type='str'),
                job_token = dict(type='str'),
                ssl_verify = dict(type='bool'),
                timeout = dict(type='float'),
                http_username = dict(type='str'),
                http_password = dict(type='str'),
                pagination = dict(type='str'),
                order_by = dict(type='str'),
                user_agent = dict(type='str'),
            ),
        ),
    ),
    )
result = dict(
    changed=False,
    diff= dict(
        before=None,
        after=dict()
    )
)
params = None
project = None
ref = None
commit = None
#############################################
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def get_clone():
    pass

def get_archive():
    global result, params, project, commit, ref
    filename = "archive"
    file_extension = '.' + params['archive']['format']
    dst = params['dest']
    if params['filename']:
        dst = "{}/{}{}".format(params['dest'], params['filename'], file_extension)
    elif params['commit_as_filename']:
        dst = "{}/{}{}".format(params['dest'], commit.short_id, file_extension)
    elif params['project_as_filename']:
        dst = "{}/{}{}".format(params['dest'], slugify(project.name), file_extension)
    else:
        dst = "{}/{}".format(params['dest'], filename)

    if params['append_project'] and not params['project_as_filename']:
        filename, file_extension = os.path.splitext(dst)
        dst = "{}-{}{}".format(filename, slugify(project.name), file_extension)
    if params['append_ref']:
        filename, file_extension = os.path.splitext(dst)
        dst = "{}-{}{}".format(filename, ref, file_extension)
    if params['append_commit'] and not params['commit_as_filename']:
        filename, file_extension = os.path.splitext(dst)
        dst = "{}-{}{}".format(filename, commit.short_id, file_extension)

    result['dest'] = dst
    result['diff']['after_header'] = dst

    if (params["state"] == "download" and (not os.path.isfile(dst)) or (params['force'])):
        if (not module.check_mode):
            # Download File
            fd, tmpsrc = tempfile.mkstemp(dir=module.tmpdir)
            try:
                with open(tmpsrc, "wb") as f:
                    project.repository_archive(
                        sha=commit.id,
                        format=params['archive']['format'],
                        streamed=True,
                        action=f.write)
                shutil.copyfile(tmpsrc, dst)
                os.remove(tmpsrc)
                result['changed'] = True
            except Exception as e:
                os.remove(tmpsrc)
                module.fail_json(msg="Failed to download file: {}".format(to_native(e)))
    msg = {
        "type": "archive",
        "project": project.name,
        "commit": commit.short_id,
        "ref": ref,
        "committed_date": commit.committed_date,
        "version": "{}-{}".format(slugify(project.name),commit.short_id),
        "filename": dst,
        "archive_path": "{}-{}".format(project.path, commit.id)
    }

    try:
        msg["filesize"] = sizeof_fmt(os.path.getsize(dst))
    except Exception as exp:
        msg["filesize"] = str(exp)
    return msg 

def get_releaase():
    pass

def get_artifact():
    global result, params, project, commit, ref
    pipeline = None
    job = None

    # Get Pipeline
    if params['artifact']['pipeline'] is not None:
        pipeline = project.pipelines.get(params['artifact']['pipeline'])
    else:
        pipelines = project.pipelines.list(ref=ref)
        if len(pipelines) < 1:
            module.fail_json(msg="No pipleline found for ref {}. ({})".format(len(pipelines), ref))
        # module.debug(json.dumps(pipelines))
        pipeline = pipelines[0]
    if not pipeline:
        module.fail_json(msg="Failed to get pipeline!")
    # Check for pipeline ref
    if (pipeline.ref != ref) and (not params['force']):
        module.fail_json(msg="Mismatch in pipline ref and provided ref ({} != {})!".format(pipeline.ref, ref))
    # Check for pipeline commit hash
    if (pipeline.sha != commit.id) and (not params['force']):
        module.fail_json(msg="Mismatch in pipline sha and commit ({} != {})!".format(pipeline.sha, commit.id))

    # Check for pipline status
    if (params['artifact']['check_pipeline_status'] and pipeline.status != params['artifact']['pipeline_status']):
        module.fail_json(msg="pipeline #{} is not in {} status ({})!".format(pipeline.id, params['artifact']['pipeline_status'] ,pipeline.status))
    # result['diff']['after']['pipeline'] = pipeline.attributes
    result['pipeline'] = pipeline.attributes

    # Get Job
    if params['artifact']['job']:
        job = project.jobs.get(params['artifact']['job'])
    else:
        jobs = pipeline.jobs.list()
        if len(jobs) < 1:
            module.fail_json(msg="Wrong number of jobs in pipeline {}. ({})".format(len(jobs), pipeline.id, ref))
        for j in jobs:
            if j.name == params['artifact']['job_name']:
                job = project.jobs.get(j.id)
                break
        if not job:
            module.fail_json(msg="Job '{}' not found in pipeline '{}'!".format(params['artifact']['job_name'], pipeline.id))

    if not job:
        result['msg'] = "Failed to get the job!"
        module.fail_json(**result)

    if (job.status != "success"):
        module.fail_json(msg="job #{} is not in success status ({})!".format(job.id, job.status))
    if (job.ref != ref) and (not params['force']):
        module.fail_json(msg="Mismatch in job ref and provided ref ({} != {})!".format(job.ref, ref))

    if (job.commit['id'] != commit.id) and (not params['force']):
        module.fail_json(msg="Mismatch in job sha and commit ({} != {})!".format(job.commit['id'], commit.id))
    if 'artifacts_file' not in job.attributes:
        module.fail_json(msg="Can not find any artifact in job {}!".format(job.id))
    result['job'] = job.attributes
    # result['diff']['after']['job'] = job.attributes

    result['diff']['after']['artifacts_file'] = job.artifacts_file
    filename, file_extension = os.path.splitext(job.artifacts_file['filename'])
    dst = params['dest']
    if params['filename']:
        dst = "{}/{}".format(params['dest'], params['filename'])
    elif params['commit_as_filename']:
        dst = "{}/{}{}".format(params['dest'], commit.short_id, file_extension)
    elif params['project_as_filename']:
        dst = "{}/{}{}".format(params['dest'], slugify(project.name), file_extension)
    else:
        dst = "{}/{}".format(params['dest'], job.artifacts_file['filename'])

    if params['append_project'] and not params['project_as_filename']:
        filename, file_extension = os.path.splitext(dst)
        dst = "{}-{}{}".format(filename, slugify(project.name), file_extension)
    if params['append_ref']:
        filename, file_extension = os.path.splitext(dst)
        dst = "{}-{}{}".format(filename, slugify(job.ref), file_extension)
    if params['append_commit'] and not params['commit_as_filename']:
        filename, file_extension = os.path.splitext(dst)
        dst = "{}-{}{}".format(filename, commit.short_id, file_extension)

    result['dest'] = dst
    result['diff']['after_header'] = dst

    if (params["state"] == "download" and (not os.path.isfile(dst)) or (params['force'])):
        if (not module.check_mode):
            # Download File
            fd, tmpsrc = tempfile.mkstemp(dir=module.tmpdir)
            try:
                with open(tmpsrc, "wb") as f:
                    job.artifacts(streamed=True, action=f.write)
                shutil.copyfile(tmpsrc, dst)
                os.remove(tmpsrc)                
                result['changed'] = True
            except Exception as e:
                os.remove(tmpsrc)
                module.fail_json(msg="Failed to download file: {}".format(to_native(e)))
    msg = {
        "type": "artifact",
        "project": project.name,
        "refrence": job.ref,
        "commit": job.commit["short_id"],
        "committed_date": job.commit["committed_date"],
        "pipeline": job.pipeline["id"],
        "pipeline_status": job.pipeline["status"],
        "pipeline_updated_at": job.pipeline["created_at"],
        "job_name": job.name,
        "job": job.id,
        "version": "{}-{}".format(slugify(project.name),job.commit["short_id"]),
        "filename": dst,
    }
    try:
        msg["filesize"] = sizeof_fmt(os.path.getsize(dst))
    except Exception as exp:
        msg["filesize"] = str(exp)
    return msg 

def main():
    global result, params, project, commit, ref
    
    params = module.params
    result["params"] = params

    dt = params["type"]

    if dt not in params:
        module.fail_json("{} variable is required for type={}".format(dt, dt))
        
    gl = gitlab.Gitlab(params['server_url'], **params['connection_options'])

    try:
        # Get Project
        project = gl.projects.get(params['project_id'])
        result['project'] = project.attributes
        if params['ref'] != '':
            ref = params['ref']
        else:
            ref = project.default_branch
        # Get Commit
        if params['commit']:
            commit = project.commits.get(params['commit'])
        else:
            commits = project.commits.list(ref_name=ref, get_all=False, per_page=1)
            if len(commits) != 1:
                module.fail_json(msg="Wrong number of commits {}. ({})".format(len(commits), ref))
            else:
                commit = commits[0]
        if not commit:
            module.fail_json(msg="Failed to get commit info.")
        result['commit'] = commit.attributes
        # result['diff']['after']['commit'] = commit.attributes

        func_name = "get_{}".format(params["type"])
        if func_name not in globals():
            module.fail_json(msg="No function found for type {}".format(params['type']))

        result['msg'] = globals()[func_name]()

        # Save Download info
        dl_info_file = "{}.json".format(result['dest'])
        if (params["state"] == "download"):
            if (not module.check_mode):
                # Download File
                fd, tmpsrc = tempfile.mkstemp(dir=module.tmpdir)
                try:
                    with open(tmpsrc, "w") as f:
                        json.dump(result['msg'], f)
                    shutil.copyfile(tmpsrc, dl_info_file)
                    os.remove(tmpsrc)                
                except Exception as e:
                    os.remove(tmpsrc)
                    module.fail_json(msg="Failed to save download info: {}".format(to_native(e)))
    except Exception as exp:
        module.fail_json(msg=str(exp))

    module.exit_json(**result)

if __name__ == '__main__':
    main()