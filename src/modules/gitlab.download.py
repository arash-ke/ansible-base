#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from tabnanny import verbose
from typing_extensions import ParamSpec

from matplotlib.font_manager import json_dump
__metaclass__ = type

import gitlab
import json
import os
import shutil
import tempfile
import traceback
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
        branch = dict(type="str", default=''),
        commit = dict(type="str"),
        dest = dict(type="str", required=True),
        filename = dict(type="str"),
        filename_prefix = dict(type="str"),
        filename_postfix = dict(type="str"),
        commit_as_filename = dict(type='bool', default=False),
        project_as_filename = dict(type='bool', default=False),
        append_commit = dict(type='bool', default=False),
        append_project = dict(type='bool', default=False),
        append_branch = dict(type='bool', default=False),
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
        connection_options = dict(
            type="dict",
            default = dict(),
            options = dict(
                private_token = dict(type='str'),
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
    global result, params, project, commit
    pipeline = None
    job = None

    # Get Pipeline
    if params['artifact']['pipeline'] is not None:
        pipeline = project.pipelines.get(params['artifact']['pipeline'])
    else:
        pipelines = project.pipelines.list(ref=params['branch'], per_page=1)
        if len(pipelines) != 1:
            module.fail_json(msg="Wrong number of pipelines {}. ({})".format(len(pipelines), params['branch']))
        pipeline = pipelines[0]
    if not pipeline:
        module.fail_json(msg="Failed to get pipeline!")
    
    if (params['branch'] != '') and (pipeline.ref != params['branch']) and (not params['force']):
        module.fail_json(msg="Mismatch in pipline ref and provided branch ({} != {})!".format(pipeline.ref, params['branch']))

    if (pipeline.sha != commit.id) and (not params['force']):
        module.fail_json(msg="Mismatch in pipline sha and commit ({} != {})!".format(pipeline.sha, commit.id))

    if (pipeline.status != "success"):
        if (pipeline.status == "running" and not params['artifact']['allow_running_pipeline']):
            pass
        else:
            module.fail_json(msg="pipeline #{} is not in success status ({})!".format(pipeline.id ,pipeline.status))
    # result['diff']['after']['pipeline'] = pipeline.attributes
    result['pipeline'] = pipeline.attributes

    if params['artifact']['job']:
        job = project.jobs.get(params['artifact']['job'])
    else:
        jobs = pipeline.jobs.list()
        if len(jobs) < 1:
            module.fail_json(msg="Wrong number of jobs in pipeline {}. ({})".format(len(jobs), pipeline.id, params['branch']))
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
    if (params['branch'] != '') and (job.ref != params['branch']) and (not params['force']):
        module.fail_json(msg="Mismatch in job ref and provided branch ({} != {})!".format(job.ref, params['branch']))

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
    if params['append_branch']:
        filename, file_extension = os.path.splitext(dst)
        dst = "{}-{}{}".format(filename, slugify(job.ref), file_extension)
    if params['append_commit'] and not params['commit_as_filename']:
        filename, file_extension = os.path.splitext(dst)
        dst = "{}-{}{}".format(filename, commit.short_id, file_extension)

    result['dest'] = dst
    result['diff']['after_header'] = dst

    if (not params['only_info'] and (not os.path.isfile(dst)) or (params['force'])):
        if (not module.check_mode):
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
        "type": "archive",
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
    }
    return msg 

def get_releaase():
    pass

def get_artifact():
    global result, params, project, commit
    pipeline = None
    job = None

    # Get Pipeline
    if params['artifact']['pipeline'] is not None:
        pipeline = project.pipelines.get(params['artifact']['pipeline'])
    else:
        pipelines = project.pipelines.list(ref=params['branch'])
        if len(pipelines) < 1:
            module.fail_json(msg="No pipleline found for ref {}. ({})".format(len(pipelines), params['branch']))
        # module.debug(json.dumps(pipelines))
        pipeline = pipelines[0]
    if not pipeline:
        module.fail_json(msg="Failed to get pipeline!")
    # Check for pipeline branch
    if (params['branch'] != '') and (pipeline.ref != params['branch']) and (not params['force']):
        module.fail_json(msg="Mismatch in pipline ref and provided branch ({} != {})!".format(pipeline.ref, params['branch']))
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
            module.fail_json(msg="Wrong number of jobs in pipeline {}. ({})".format(len(jobs), pipeline.id, params['branch']))
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
    if (params['branch'] != '') and (job.ref != params['branch']) and (not params['force']):
        module.fail_json(msg="Mismatch in job ref and provided branch ({} != {})!".format(job.ref, params['branch']))

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
    if params['append_branch']:
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
    global result, params, project, commit 
    
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
        
        # Get Commit
        if params['commit']:
            commit = project.commits.get(params['commit'])
        else:
            commits = project.commits.list(ref_name=params['branch'], per_page=1)
            if len(commits) != 1:
                module.fail_json(msg="Wrong number of commits {}. ({})".format(len(commits), params['branch']))
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